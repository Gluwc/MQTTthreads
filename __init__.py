# -*- coding: utf-8 -*-
#
# plugins/MQTT Client/__init__.py
#
# This file is a plugin for EventGhost.
# Copyright (C) 2016 Walter Kraembring <krambriw>.
#
###############################################################################
#
# EventGhost is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation;
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Revision history:
#
# 2017-02-07  Added action to support publishing of binary data like pictures
# 2016-12-15  Modified decoding of Domoticz events for Motion SensorS
# 2016-11-28  Added support for username & password/key authentication
#             Added support for TLS/SSL
# 2016-10-15  Modified decoding of Domoticz events for on/off switches
# 2016-10-07  Added support for Domoticz
# 2016-08-13  Fixed a compatibilty issue for EG version 0.5.x (AddGrowableCol)
# 2016-06-06  Modified the publishMQTT action
# 2016-05-17  With support for openHAB (Use topic /openHAB/)
# 2016-02-24  Migrated, now using Paho instead of Mosquitto
# 2016-02-18  Improved handling of topics (no need to have leading slash (/))
#             Supporting subscription to # (not recommended)
# 2015-05-28  Added support for Node-RED MQTT events (NRED)
# 2015-05-12  Added support for SwitchKing MQTT events
# 2015-01-18  Had to change the logic for handling possible duplicates of MQTT
#             subscriptions. Now only recommending not to run duplicates, not
#             preventing.
# 2014-12-05  Some clean up in handling and running MQTT subscriptions.
#             Avoiding duplicates of MQTT subscriptions
# 2014-11-29  Added option to select if event string and payload should be
#             linked together as combined event content
# 2014-07-31  Changed event prefix to 'MQTT'
#             Added support for utf-8 encoding/decoding
# 2014-04-30  Improved error message contents
# 2014-03-10  Added client connection retry handling
# 2014-01-12  Added timed dictionary to avoid duplicates
# 2013-10-20  The first stumbling version
##############################################################################
#
# Acknowledgement: All credits to Mr Roger Light <roger@atchoo.org> and
# The Eclipse Foundation project for the Eclipse Paho MQTT Python client
# library
#
##############################################################################

eg.RegisterPlugin(
    name = "MQTT Client",
    author = "Walter Kraembring (krambriw)",
    version = "1.1.0",
    canMultiLoad = False,
    kind = "other",
    url = "http://www.eventghost.org",
    description = ("Eclipse Paho MQTT Python client library implements"+
                   "versions 3.1 and 3.1.1 of the MQTT protocol."+
                   "This enables applications to connect to an MQTT broker"+
                   "to publish messages, and to subscribe to topics and"+
                   "receive published messages."+
                   "The MQTT protocol is a machine-to-machine connectivity"+
                   "protocol. Designed as an extremely lightweight"+
                   "publish/subscribe messaging transport, it is useful for"+
                   "connections with remote locations where a small code"+
                   "footprint is required and/or network bandwidth is at a"+
                   "premium."
    ),
    guid = "{D5CCABA6-8E20-4B59-A7A7-9C197F91037F}"
)

import paho.mqtt.client as mqtt
#import paho.mqtt.publish as publish
import time
import random
from threading import Event, Thread
from ast import literal_eval



class Text:
    started = "Plugin started"
    listhl = "Currently active threads:"
    colLabels = (
        "MQTT Subscriber Name ",
        "MQTT client id       ",
        "MQTT broker host/ip  ",
        "Port                 ",
        "Persistent session   ",
        "Topic                ",
        "                     "
    )

    #Buttons
    b_abort = "Abort"
    b_abortAll = "Abort all"
    b_restartAll = "Restart All"
    b_refresh = "Refresh"

    #Threads
    n_ThreadMQTT = "MQTT Client"
    thr_abort = "Thread is terminating: "
    connection_problem = 'MQTT Client: Trying to reconnect with...'
    connected = 'Succesfully connected with MQTT broker...'


class MQTTclientTxt:
    name = "Start a new MQTT subscription "
    description = ("A MQTT subscriber")
    actionName = "MQTT subscriber name: "
    hostName =   "Host ip or name: "
    portName =   "Port number:      "
    topicName =  "Topic: "
    tTopic = "Check to include payload in event string: "
    pSession = "Check to make a persistent session: "
    used_sub = 'MQTT subscription is already existing and running, duplicates are not recommended'
    ucred = "Use credentials: "
    username = "User name: "
    password = "Password/Key: "
    utls = "Use TLS/SSL: "
    certs = "Path to certificate: "


class publishMQTTtxt:
    name = "Publish a MQTT message"
    description = ("A MQTT message")
    empty = '>>EMPTY<<'
    actionName =  "MQTT publisher name: "
    hostName =    "Host ip or name: "
    portName =    "Port number:      "
    topicName =   "Topic: "
    messageName = "Message: "
    qosName =     "QOS:                   "
    retainName =  "Retain:                "
    ucred = "Use credentials: "
    username = "User name: "
    password = "Password/Key: "
    utls = "Use TLS/SSL: "
    certs = "Path to certificate: "


class publishBinaryMQTTtxt:
    name = "Publish a binary file as MQTT message"
    description = ("A MQTT binary message")
    empty = '>>EMPTY<<'
    actionName =  "MQTT publisher name: "
    hostName =    "Host ip or name: "
    portName =    "Port number:      "
    topicName =   "Topic: "
    fileName = "Select file: "
    toolTipFile = "Press button and browse to select a file ..."
    browseFile = 'Select the file'
    qosName =     "QOS:                   "
    retainName =  "Retain:                "
    ucred = "Use credentials: "
    username = "User name: "
    password = "Password/Key: "
    utls = "Use TLS/SSL: "
    certs = "Path to certificate: "




class ThreadMQTT(Thread):
    text = Text

    def __init__(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
 ):
        Thread.__init__(self, name = self.text.n_ThreadMQTT)
        self.name = name
        self.host = host
        self.port = port
        self.ucred = ucred
        self.username = username
        self.password = password
        self.utls = utls
        self.ca_certs = ca_certs
        self.topic = topic
        self.topicTrigger = topicTrigger
        self.cid = cid
        self.persistentSession = persistentSession
        self.finished = Event()
        self.abort = False
        self.eventCollection = []
        self.eventCollection = {}
        self.taskObj = {}
        self.bDelayRepeat = False
        self.delayRepeat = 1.0
        self.prefix = 'MQTT'


    def run(self):

        def RemoveEventFromCollection(t_key, res_key):
            try:
                del self.taskObj[t_key]
                self.eventCollection[res_key] = ''
            except:
                pass


        def TriggerEvent(msg):
            smsg = msg.topic.decode('utf-8')
            pl = str(msg.payload).decode('utf-8')
            if self.topicTrigger:
                smsg = smsg + '.' + pl
            eg.TriggerEvent(
                smsg,
                payload = pl,
                prefix=self.prefix
            )


        def ProcessEvent(msg, bDelay, delay, res_key, res_base):
            try:
                v = self.eventCollection[res_key]
            except KeyError:
                self.eventCollection[res_key] = ''

            if self.eventCollection[res_key] != res_base:
                if bDelay:
                    self.eventCollection[res_key] = res_base
                TriggerEvent(msg)
                self.bDelayRepeat = bDelay
                self.delayRepeat = delay

                if self.bDelayRepeat:
                    #Schedule the event removal task
                    t_key = str(time.time())
                    p = eg.scheduler.AddTask(
                        self.delayRepeat,
                        RemoveEventFromCollection,
                        t_key, res_key
                    )
                    self.taskObj[t_key] = str(p)
            return


        def ProcessEvent2(msg, bDelay, delay, res_key, result):
            try:
                v = self.eventCollection[res_key]
            except KeyError:
                self.eventCollection[res_key] = ''

            if self.eventCollection[res_key] != result:
                if bDelay:
                    self.eventCollection[res_key] = result
                TriggerEvent2(msg, result)
                self.bDelayRepeat = bDelay
                self.delayRepeat = delay

                if self.bDelayRepeat:
                    #Schedule the event removal task
                    t_key = str(time.time())
                    p = eg.scheduler.AddTask(
                        self.delayRepeat,
                        RemoveEventFromCollection,
                        t_key, res_key
                    )
                    self.taskObj[t_key] = str(p)
            return


        def TriggerEvent2(msg, result):
            smsg = (msg.topic.decode('utf-8')+
                '/'+
                str(result[2])+
                '/'+
                str(result[4])
            )
            if result[-2] == "On/Off" or result[-2] == "Motion Sensor":
                smsg = (msg.topic.decode('utf-8')+
                    '/'+
                    str(result[2])+
                    '/'+
                    str(result[4])+
                    '/'+
                    str(result[6])
                )
            eg.TriggerEvent(
                smsg,
                payload = result,
                prefix=self.prefix
            )


        def on_connect(client, userdata, flags, rc):
            #print flags
            qos = 0
            if self.persistentSession:
                qos = 2
            client.subscribe((str(self.topic), qos))


        def on_subscribe(client, userdata, mid, granted_qos):
            #print("Subscribed: "+str(mid)+" "+str(granted_qos))
            pass


        def on_message(client, userdata, msg):
            if msg.topic.find('domoticz') != -1:
                event = literal_eval(msg.payload)
                result = []
                allowed = [
                    "Battery",
                    "RSSI",
                    "dtype",
                    "id",
                    "idx",
                    "name",
                    "nvalue",
                    "stype",
                    "svalue1",
                    "svalue2",
                    "switchType",
                    "unit"
                ]
                for item in allowed:
                    try:
                        result.append(event[item])
                    except:
                        pass
                res_key = msg.topic + ', ' + str(result[4])
                res_base = str(msg.qos)+" "+str(result)
                ProcessEvent2(msg, False, 0.0, res_key, result)
                return

            if self.topic.find('/openHAB/') != -1:
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, False, 0.0, res_key, event)
                return

            if self.topic == '#':
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, event)
                return

            if str(msg.topic) == self.topic:
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, event)
                return

            if (
                self.topic.find('/#') > 0
                and
                str(msg.topic).find(self.topic.split('/#')[0]) > -1
            ):
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 5.0, res_key, event)
                return

            if str(msg.topic).find('zwave') > 0:
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 10.0, res_key, event)
                return

            if str(msg.topic).find('rfxtrx') > 0:
                event = str(msg.payload).split('id: ')
                res_key = msg.topic + ', ' + event[1].split(',')[0]
                res_base = str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, event)
                return

            if str(msg.topic).find('nethomeserver') > 0:
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, event)
                return

            if str(msg.topic).find('switchking') > -1:
                event = msg.payload
                res_key = str(msg.topic) + ', ' + str(msg.payload)
                res_base = str(msg.qos) + " "+ str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, res_base)
                return

            if str(msg.topic).find('NRED') > -1:
                event = msg.payload
                res_key = str(msg.topic) + ', ' + str(msg.payload)
                res_base = str(msg.qos) + " "+ str(msg.payload)
                ProcessEvent(msg, True, 1.0, res_key, res_base)
                return

            if str(msg.topic).find(self.topic.split('/')[1]) > 0:
                event = str(msg.payload).split(',')
                res_key = msg.topic + ', ' + event[0]
                res_base = str(msg.qos)+" "+str(msg.payload)
                ProcessEvent(msg, True, 5.0, res_key, event)
                return

        cs = 1
        if self.persistentSession:
            cs = 0

        mqttc = mqtt.Client(
            str(self.cid),
            clean_session=cs,
            userdata=None,
            protocol=4
        )
        mqttc.on_message = on_message
        mqttc.on_connect = on_connect
        mqttc.on_subscribe = on_subscribe
        resp = None

        while resp <> 0 and self.abort == False:
            lrsp = 0
            try:
                if self.ucred:
                    mqttc.username_pw_set(self.username, self.password)
                if self.utls:
                    try:
                        f = open(self.ca_certs, "r")
                        f.close()
                        mqttc.tls_set(self.ca_certs)
                    except IOError as err:
                        eg.PrintError("No certificate found")
                resp = mqttc.connect(self.host, self.port, 60)
            except:
                pass
            if resp <> 0:
                print self.text.connection_problem +self.topic +' ' +self.host
                self.finished.wait(5.0)
            else:
                pass
                #print 'MQTT Client ', self.name +':', self.text.connected
            while lrsp == 0 and self.abort == False:
                lrsp = mqttc.loop(10.0, 1)
                #print 'lrsp', lrsp
                self.finished.wait(0.01)
                #self.finished.clear()
                if lrsp <> 0:
                    resp = -1
                    mqttc.disconnect()
                if self.abort:
                    mqttc.disconnect()
                    self.finished.wait(1.0)
                    break
            self.finished.wait(10.0)
            self.finished.clear()


    def CancelTasks(self):
        for key in self.taskObj:
            try:
                eg.scheduler.CancelTask(key)
            except ValueError:
                pass
        self.taskObj = {}


    def AbortMQTT(self):
        print self.text.thr_abort, self.text.n_ThreadMQTT
        self.abort = True
        self.finished.set()
        time.sleep(0.1)
        self.CancelTasks()



class MQTTthreads(eg.PluginClass):
    text = Text

    def __init__(self):
        self.AddAction(MQTTclient)
        self.AddAction(publishMQTT)
        self.AddAction(publishBinaryMQTT)
        self.AllMQTTsubscribers = []
        self.lastMQTTName = ""
        self.MQTTThreads = {}
        self.OkButtonClicked = False
        self.started = False


    def __start__(
        self
    ):
        print self.text.started

        if self.OkButtonClicked:
            self.OkButtonClicked = False
            self.RestartAllMQTTs()

        self.mainThreadEvent = Event()
        mainThread = Thread(target=self.main, args=(self.mainThreadEvent,))
        mainThread.start()
        self.started = True


    def __stop__(self):
        self.mainThreadEvent.set()
        self.AbortAllMQTTs()
        self.started = False


    def __close__(self):
        self.AbortAllMQTTs()
        self.started = False


    def main(self,mainThreadEvent):
        while not mainThreadEvent.isSet():
            self.mainThreadEvent.wait(10.0)
            #print "Main thread is running..."


    #methods to Control MQTTs
    def StartMQTTs(
        self,
        MQTTName,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        if self.MQTTThreads.has_key(MQTTName):
            t = self.MQTTThreads[MQTTName]
            if t.isAlive():
                t.AbortMQTT()
            del self.MQTTThreads[MQTTName]
        t = ThreadMQTT(
            MQTTName,
            host,
            port,
            topic,
            topicTrigger,
            cid,
            persistentSession,
            ucred,
            username,
            password,
            utls,
            ca_certs
        )
        self.MQTTThreads[MQTTName] = t
        self.AddMQTTsubscriber(
            MQTTName,
            host,
            port,
            topic,
            topicTrigger,
            cid,
            persistentSession,
            ucred,
            username,
            password,
            utls,
            ca_certs
        )
        t.start()


    def AbortMQTT(self, MQTT):
        if self.MQTTThreads.has_key(MQTT):
            t = self.MQTTThreads[MQTT]
            t.AbortMQTT()
            del self.MQTTThreads[MQTT]


    def AbortAllMQTTs(self):
        for i, item in enumerate(self.MQTTThreads):
            t = self.MQTTThreads[item]
            t.AbortMQTT()
            del t
        self.MQTTThreads = {}


    def RestartAllMQTTs(self, startNewIfNotAlive = True):
        self.AbortAllMQTTs()
        for item in self.GetAllMQTTsubscribers():
            item = item.split(',')
            if startNewIfNotAlive:
                bT = True
                bP = False
                bC = False
                bU = False
                if item[4] == 'False':
                    bT = False
                if item[6] == 'True':
                    bP = True
                if item[7] == 'True':
                    bC = True
                if item[10] == 'True':
                    bU = True
                self.StartMQTTs(
                    item[0],
                    item[1],
                    int(item[2]),
                    item[3],
                    bT,
                    item[5],
                    bP,
                    bC,
                    item[8],
                    item[9],
                    bU,
                    item[11]
                )


    def Configure(
        self,
        *args
    ):
        panel = eg.ConfigPanel(self, resizable=True)

        panel.sizer.Add(
            wx.StaticText(panel, -1, self.text.listhl),
            flag = wx.ALIGN_CENTER_VERTICAL
        )

        mySizer = wx.GridBagSizer(5, 5)

        testListCtrl = wx.ListCtrl(
            panel,
            -1,
            style=wx.LC_REPORT | wx.VSCROLL | wx.HSCROLL
        )

        for i, colLabel in enumerate(self.text.colLabels):
            testListCtrl.InsertColumn(i, colLabel)

        #setting col width to fit label
        testListCtrl.InsertStringItem(0, "Test Subscriber Name               ")
        testListCtrl.SetStringItem(0, 1, "                                   ")
        testListCtrl.SetStringItem(0, 2, "                                   ")
        testListCtrl.SetStringItem(0, 3, "                                   ")
        testListCtrl.SetStringItem(0, 4, "                                   ")
        testListCtrl.SetStringItem(0, 5, "                                   ")
        testListCtrl.SetStringItem(0, 6, "                                   ")

        size = 0
        for i in range(6):
            testListCtrl.SetColumnWidth(
                i,
                wx.LIST_AUTOSIZE_USEHEADER
            ) #wx.LIST_AUTOSIZE
            size += testListCtrl.GetColumnWidth(i)

        testListCtrl.SetMinSize((size, -1))

        mySizer.Add(testListCtrl, (0,0), (1, 5), flag = wx.EXPAND)

        #buttons
        abortButton = wx.Button(panel, -1, self.text.b_abort)
        mySizer.Add(abortButton, (3,0))

        abortAllButton = wx.Button(panel, -1, self.text.b_abortAll)
        mySizer.Add(abortAllButton, (3,1), flag = wx.ALIGN_RIGHT)

        restartAllButton = wx.Button(panel, -1, self.text.b_restartAll)
        mySizer.Add(restartAllButton, (3,2), flag = wx.ALIGN_RIGHT)

        refreshButton = wx.Button(panel, -1, self.text.b_refresh)
        mySizer.Add(refreshButton, (3,4), flag = wx.ALIGN_RIGHT)

        mySizer.AddGrowableRow(0)
        mySizer.AddGrowableCol(0)
        mySizer.AddGrowableCol(1)
        mySizer.AddGrowableCol(2)
        mySizer.AddGrowableCol(3)
        mySizer.AddGrowableCol(4)

        panel.sizer.Add(mySizer, 1, flag = wx.EXPAND)


        def PopulateList (event):
            testListCtrl.DeleteAllItems()
            row = 0
            for i, item in enumerate(self.MQTTThreads):
                t = self.MQTTThreads[item]
                if t.isAlive():
                    testListCtrl.InsertStringItem(
                        row,
                        t.name
                    )
                    testListCtrl.SetStringItem(row,
                        1, t.cid)
                    testListCtrl.SetStringItem(row,
                        2, t.host)
                    testListCtrl.SetStringItem(row,
                        3, str(t.port))
                    testListCtrl.SetStringItem(row,
                        4, str(t.persistentSession))
                    testListCtrl.SetStringItem(row,
                        5, t.topic)
                    row += 1
            ListSelection(wx.CommandEvent())


        def OnAbortButton(event):
            item = testListCtrl.GetFirstSelected()
            while item != -1:
                name = testListCtrl.GetItemText(item)
                self.AbortMQTT(name)
                item = testListCtrl.GetNextSelected(item)
            PopulateList(wx.CommandEvent())
            event.Skip()


        def OnAbortAllButton(event):
            self.AbortAllMQTTs()
            PopulateList(wx.CommandEvent())
            event.Skip()


        def OnRestartAllButton(event):
            self.RestartAllMQTTs()
            PopulateList(wx.CommandEvent())
            event.Skip()


        def ListSelection(event):
            flag = testListCtrl.GetFirstSelected() != -1
            abortButton.Enable(flag)
            event.Skip()


        def OnSize(event):
            testListCtrl.SetColumnWidth(
                6,
                wx.LIST_AUTOSIZE_USEHEADER
            ) #wx.LIST_AUTOSIZE
            event.Skip()


        def OnApplyButton(event):
            event.Skip()
            self.RestartAllMQTTs()
            PopulateList(wx.CommandEvent())


        def OnOkButton(event):
            event.Skip()
            self.OkButtonClicked = True
            if not self.started:
                self.RestartAllMQTTs()
            PopulateList(wx.CommandEvent())


        PopulateList(wx.CommandEvent())
        abortButton.Bind(wx.EVT_BUTTON, OnAbortButton)
        abortAllButton.Bind(wx.EVT_BUTTON, OnAbortAllButton)
        restartAllButton.Bind(wx.EVT_BUTTON, OnRestartAllButton)
        refreshButton.Bind(wx.EVT_BUTTON, PopulateList)
        testListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, ListSelection)
        testListCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, ListSelection)
        panel.Bind(wx.EVT_SIZE, OnSize)
        panel.dialog.buttonRow.applyButton.Bind(wx.EVT_BUTTON, OnApplyButton)
        panel.dialog.buttonRow.okButton.Bind(wx.EVT_BUTTON, OnOkButton)

        while panel.Affirmed():
            panel.SetResult(
                        *args
            )


    def GetAllMQTTsubscribers(self):
        return self.AllMQTTsubscribers


    def AddMQTTsubscriber(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        sub = (
            name+','+
            host+','+
            str(port)+','+
            topic+','+
            str(topicTrigger)+','+
            cid+','+
            str(persistentSession)+','+
            str(ucred)+','+
            username+','+
            password+','+
            str(utls)+','+
            ca_certs
        )
        if not sub in self.AllMQTTsubscribers:
            self.AllMQTTsubscribers.append(sub)
        return self.AllMQTTsubscribers.index(sub)


    def DelMQTTsubscriber(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        sub = (
            name+','+
            host+','+
            str(port)+','+
            topic+','+
            str(topicTrigger)+','+
            cid+','+
            str(persistentSession)+','+
            str(ucred)+','+
            username+','+
            password+','+
            str(utls)+','+
            ca_certs
        )
        if sub in self.AllMQTTsubscribers:
            self.AllMQTTsubscribers.remove(sub)


    def CheckMQTTsubscriber(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        sub = (
            name+','+
            host+','+
            str(port)+','+
            topic+','+
            str(topicTrigger)+','+
            cid+','+
            str(persistentSession)+','+
            str(ucred)+','+
            username+','+
            password+','+
            str(utls)+','+
            ca_certs
        )
        for item in self.AllMQTTsubscribers:
            lst = item.split(',')
            if lst[5] == cid:
                return True
        return False



class MQTTclient(eg.ActionClass):
    text = MQTTclientTxt
    chk = False

    def __call__(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        self.plugin.StartMQTTs(
            name,
            host,
            port,
            topic,
            topicTrigger,
            cid,
            persistentSession,
            ucred,
            username,
            password,
            utls,
            ca_certs
        )


    def GetLabel(
        self,
        name,
        host,
        port,
        topic,
        topicTrigger,
        cid,
        persistentSession,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        print self.text.labelStart % (name)
        return self.text.labelStart % (name)


    def Configure(
        self,
        name="Give this MQTT subscriber a name",
        host="test.mosquitto.org",
        port=1883,
        topic="eventghost",
        topicTrigger=False,
        cid="",
        persistentSession=False,
        ucred=False,
        username="username",
        password="password",
        utls=False,
        ca_certs=""
    ):
        plugin = self.plugin
        panel = eg.ConfigPanel(self)
        mySizer_1 = wx.GridBagSizer(10, 10)
        mySizer_2 = wx.GridBagSizer(10, 10)
        mySizer_3 = wx.GridBagSizer(10, 10)
        mySizer_4 = wx.GridBagSizer(10, 10)
        mySizer_5 = wx.GridBagSizer(10, 10)
        mySizer_6 = wx.GridBagSizer(10, 10)
        mySizer_7 = wx.GridBagSizer(10, 10)

        #name
        nameCtrl = wx.TextCtrl(panel, -1, name)
        nameCtrl.SetInitialSize((250,-1))
        mySizer_1.Add(wx.StaticText(panel, -1, self.text.actionName), (0,0))
        mySizer_1.Add(nameCtrl, (1,0))

        #host
        hostCtrl = wx.TextCtrl(panel, -1, host)
        hostCtrl.SetInitialSize((150,-1))
        mySizer_2.Add(wx.StaticText(panel, -1, self.text.hostName), (1,0))
        mySizer_2.Add(hostCtrl, (1,1))

        #port
        portCtrl = panel.SpinIntCtrl(port)
        portCtrl.SetInitialSize((75,-1))
        mySizer_3.Add(wx.StaticText(panel, -1, self.text.portName), (1,0))
        mySizer_3.Add(portCtrl, (1,1))

        #topic
        topicCtrl = wx.TextCtrl(panel, -1, topic)
        topicCtrl.SetInitialSize((250,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.topicName), (1,0))
        mySizer_4.Add(topicCtrl, (2,0))

        #topic Trigger
        tTopicCtrl = wx.CheckBox(panel, -1, "")
        tTopicCtrl.SetValue(topicTrigger)
        mySizer_5.Add(wx.StaticText(panel, -1, self.text.tTopic), (1,0))
        mySizer_5.Add(tTopicCtrl, (2,0))

        #use credentials
        ucredCtrl = wx.CheckBox(panel, -1, "")
        ucredCtrl.SetValue(ucred)
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.ucred), (1,0))
        mySizer_6.Add(ucredCtrl, (2,0))

        #user
        userCtrl = wx.TextCtrl(panel, -1, username)
        userCtrl.SetInitialSize((250,-1))
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.username), (3,0))
        mySizer_6.Add(userCtrl, (4,0))

        #password/key
        pwordCtrl = wx.TextCtrl(panel, -1, password)
        pwordCtrl.SetInitialSize((250,-1))
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.password), (5,0))
        mySizer_6.Add(pwordCtrl, (6,0))

        #use TLS/SSL
        utlsCtrl = wx.CheckBox(panel, -1, "")
        utlsCtrl.SetValue(utls)
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.utls), (7,0))
        mySizer_6.Add(utlsCtrl, (8,0))

        #path to cert
        certsCtrl = wx.TextCtrl(panel, -1, ca_certs)
        certsCtrl.SetInitialSize((400,-1))
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.certs), (9,0))
        mySizer_6.Add(certsCtrl, (10,0))

        #persistentSession
        pSessionCtrl = wx.CheckBox(panel, -1, "")
        pSessionCtrl.SetValue(persistentSession)
        mySizer_7.Add(wx.StaticText(panel, -1, self.text.pSession), (1,0))
        mySizer_7.Add(pSessionCtrl, (2,0))

        panel.sizer.Add(mySizer_1, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_2, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_3, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_6, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_4, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_5, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_7, 0, flag = wx.EXPAND)

        if cid == '':
            random.jumpahead(168)
            tr = random.random()
            cid = str(tr).split('.')[1]

        def OnButton(event):
            # re-assign the OK button
            event.Skip()
            name = nameCtrl.GetValue()
            host = hostCtrl.GetValue()
            port = portCtrl.GetValue()
            topic = topicCtrl.GetValue()
            topicTrigger = tTopicCtrl.GetValue()
            persistentSession = pSessionCtrl.GetValue()
            ucred = ucredCtrl.GetValue()
            username = userCtrl.GetValue()
            password = pwordCtrl.GetValue()
            utls = utlsCtrl.GetValue()
            ca_certs = certsCtrl.GetValue()

            self.chk = plugin.CheckMQTTsubscriber(
                name,
                host,
                port,
                topic,
                topicTrigger,
                cid,
                persistentSession,
                ucred,
                username,
                password,
                utls,
                ca_certs
            )

            plugin.lastMQTTName = name
            plugin.AddMQTTsubscriber(
                name,
                host,
                port,
                topic,
                topicTrigger,
                cid,
                persistentSession,
                ucred,
                username,
                password,
                utls,
                ca_certs
            )
            plugin.RestartAllMQTTs()

            if self.chk:
                eg.PrintError(self.text.used_sub)

        panel.dialog.buttonRow.okButton.Bind(wx.EVT_BUTTON, OnButton)

        plugin.DelMQTTsubscriber(
            name,
            host,
            port,
            topic,
            topicTrigger,
            cid,
            persistentSession,
            ucred,
            username,
            password,
            utls,
            ca_certs
        )

        while panel.Affirmed():
            name = nameCtrl.GetValue()
            host = hostCtrl.GetValue()
            port = portCtrl.GetValue()
            topic = topicCtrl.GetValue()
            topicTrigger = tTopicCtrl.GetValue()
            persistentSession = pSessionCtrl.GetValue()
            ucred = ucredCtrl.GetValue()
            username = userCtrl.GetValue()
            password = pwordCtrl.GetValue()
            utls = utlsCtrl.GetValue()
            ca_certs = certsCtrl.GetValue()

            panel.SetResult(
                name,
                host,
                port,
                topic,
                topicTrigger,
                cid,
                persistentSession,
                ucred,
                username,
                password,
                utls,
                ca_certs
            )



class publishMQTT(eg.ActionClass):
    text = publishMQTTtxt

    def __call__(
        self,
        name,
        host,
        port,
        topic,
        message,
        qos,
        retain,
        cid,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        self.name = name
        self.cid = cid
        self.host = host
        self.port = port
        self.ucred = ucred
        self.username = username
        self.password = password
        self.utls = utls
        self.ca_certs = ca_certs
        self.topic = topic
        self.message = str(
            (eg.ParseString(message) if message else '').encode("utf-8")
        )
        self.qos = qos
        self.retain = retain
        self.clean_session = 1
        if self.qos > 0:
            self.clean_session = 0

        mqttc = mqtt.Client(
            str(self.cid),
            clean_session=self.clean_session,
            userdata=None,
            protocol=4
        )

        if self.ucred:
            mqttc.username_pw_set(self.username, self.password)

        if self.utls:
            try:
                f = open(self.ca_certs, "r")
                f.close()
                mqttc.tls_set(self.ca_certs)
            except IOError as err:
                eg.PrintError("No certificate found")

        mqttc.connect(
            host=self.host,
            port=self.port,
            keepalive=60,
            bind_address=""
        )

        mqttc.publish(
            topic=self.topic,
            payload=self.message,
            qos=self.qos,
            retain=self.retain
        )

        time.sleep(0.05)
        mqttc.disconnect()


    def Configure(
        self,
        name="Give this MQTT message a name",
        host="test.mosquitto.org",
        port=1883,
        topic="eventghost",
        message=u"{eg.event.string}",
        qos=0,
        retain=False,
        cid='',
        ucred=False,
        username="username",
        password="password",
        utls=False,
        ca_certs=""
    ):
        plugin = self.plugin
        panel = eg.ConfigPanel(self)
        mySizer_1 = wx.GridBagSizer(10, 10)
        mySizer_2 = wx.GridBagSizer(10, 10)
        mySizer_3 = wx.GridBagSizer(10, 10)
        mySizer_4 = wx.GridBagSizer(10, 10)
        mySizer_5 = wx.GridBagSizer(10, 10)
        mySizer_6 = wx.GridBagSizer(10, 10)
        mySizer_7 = wx.GridBagSizer(10, 10)
        mySizer_8 = wx.GridBagSizer(10, 10)

        #name
        nameCtrl = wx.TextCtrl(panel, -1, name)
        nameCtrl.SetInitialSize((250,-1))
        mySizer_1.Add(wx.StaticText(panel, -1, self.text.actionName), (0,0))
        mySizer_1.Add(nameCtrl, (1,0))

        #host
        hostCtrl = wx.TextCtrl(panel, -1, host)
        hostCtrl.SetInitialSize((150,-1))
        mySizer_2.Add(wx.StaticText(panel, -1, self.text.hostName), (1,0))
        mySizer_2.Add(hostCtrl, (1,1))

        #port
        portCtrl = panel.SpinIntCtrl(port)
        portCtrl.SetInitialSize((75,-1))
        mySizer_3.Add(wx.StaticText(panel, -1, self.text.portName), (1,0))
        mySizer_3.Add(portCtrl, (1,1))

        #use credentials
        ucredCtrl = wx.CheckBox(panel, -1, "")
        ucredCtrl.SetValue(ucred)
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.ucred), (1,0))
        mySizer_4.Add(ucredCtrl, (2,0))

        #user
        userCtrl = wx.TextCtrl(panel, -1, username)
        userCtrl.SetInitialSize((250,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.username), (3,0))
        mySizer_4.Add(userCtrl, (4,0))

        #password/key
        pwordCtrl = wx.TextCtrl(panel, -1, password)
        pwordCtrl.SetInitialSize((250,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.password), (5,0))
        mySizer_4.Add(pwordCtrl, (6,0))

        #use TLS/SSL
        utlsCtrl = wx.CheckBox(panel, -1, "")
        utlsCtrl.SetValue(utls)
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.utls), (7,0))
        mySizer_4.Add(utlsCtrl, (8,0))

        #path to cert
        certsCtrl = wx.TextCtrl(panel, -1, ca_certs)
        certsCtrl.SetInitialSize((400,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.certs), (9,0))
        mySizer_4.Add(certsCtrl, (10,0))

        #topic
        topicCtrl = wx.TextCtrl(panel, -1, topic)
        topicCtrl.SetInitialSize((250,-1))
        mySizer_5.Add(wx.StaticText(panel, -1, self.text.topicName), (1,0))
        mySizer_5.Add(topicCtrl, (2,0))

        #message
        messageCtrl = wx.TextCtrl(panel, -1, message)
        messageCtrl.SetInitialSize((250,-1))
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.messageName), (1,0))
        mySizer_6.Add(messageCtrl, (2,0))

        #qos
        qosCtrl = panel.SpinIntCtrl(qos, min=0, max=2)
        qosCtrl.SetInitialSize((50,-1))
        mySizer_7.Add(wx.StaticText(panel, -1, self.text.qosName), (1,0))
        mySizer_7.Add(qosCtrl, (1,1))

        #retain
        retainCtrl = wx.CheckBox(panel, -1, '')
        retainCtrl.SetValue(retain)
        retainCtrl.SetInitialSize((50,-1))
        mySizer_8.Add(wx.StaticText(panel, -1, self.text.retainName), (1,0))
        mySizer_8.Add(retainCtrl, (1,1))

        panel.sizer.Add(mySizer_1, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_2, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_3, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_4, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_5, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_6, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_7, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_8, 0, flag = wx.EXPAND)

        if cid == '':
            random.jumpahead(168)
            tr = random.random()
            cid = str(tr).split('.')[1]

        while panel.Affirmed():
            name = nameCtrl.GetValue()
            host = hostCtrl.GetValue()
            port = portCtrl.GetValue()
            ucred = ucredCtrl.GetValue()
            username = userCtrl.GetValue()
            password = pwordCtrl.GetValue()
            utls = utlsCtrl.GetValue()
            ca_certs = certsCtrl.GetValue()
            topic = topicCtrl.GetValue()
            message = messageCtrl.GetValue()
            qos = qosCtrl.GetValue()
            retain = retainCtrl.GetValue()
            panel.SetResult(
                name,
                host,
                port,
                topic,
                message,
                qos,
                retain,
                cid,
                ucred,
                username,
                password,
                utls,
                ca_certs
            )



class publishBinaryMQTT(eg.ActionClass):
    text = publishBinaryMQTTtxt

    def __call__(
        self,
        name,
        host,
        port,
        topic,
        bfile,
        qos,
        retain,
        cid,
        ucred,
        username,
        password,
        utls,
        ca_certs
    ):
        self.name = name
        self.cid = cid
        self.host = host
        self.port = port
        self.ucred = ucred
        self.username = username
        self.password = password
        self.utls = utls
        self.ca_certs = ca_certs
        self.topic = topic
        self.bfile = bfile

        pic = open(self.bfile, 'rb')
        imagestring = pic.read()
        byteArray = bytearray(imagestring)
        pic.close()

        self.qos = qos
        self.retain = retain
        self.clean_session = 1
        if self.qos > 0:
            self.clean_session = 0

        mqttc = mqtt.Client(
            str(self.cid),
            clean_session=self.clean_session,
            userdata=None,
            protocol=4
        )

        if self.ucred:
            mqttc.username_pw_set(self.username, self.password)

        if self.utls:
            try:
                f = open(self.ca_certs, "r")
                f.close()
                mqttc.tls_set(self.ca_certs)
            except IOError as err:
                eg.PrintError("No certificate found")

        mqttc.connect(
            host=self.host,
            port=self.port,
            keepalive=60,
            bind_address=""
        )

        mqttc.publish(
            topic=self.topic,
            payload=byteArray,
            qos=self.qos,
            retain=self.retain
        )

        time.sleep(0.05)
        mqttc.disconnect()


    def Configure(
        self,
        name="Give this MQTT message a name",
        host="test.mosquitto.org",
        port=1883,
        topic="eventghost",
        bfile="",
        qos=0,
        retain=False,
        cid='',
        ucred=False,
        username="username",
        password="password",
        utls=False,
        ca_certs=""
    ):
        plugin = self.plugin
        panel = eg.ConfigPanel(self)
        mySizer_1 = wx.GridBagSizer(10, 10)
        mySizer_2 = wx.GridBagSizer(10, 10)
        mySizer_3 = wx.GridBagSizer(10, 10)
        mySizer_4 = wx.GridBagSizer(10, 10)
        mySizer_5 = wx.GridBagSizer(10, 10)
        mySizer_6 = wx.GridBagSizer(10, 10)
        mySizer_7 = wx.GridBagSizer(10, 10)
        mySizer_8 = wx.GridBagSizer(10, 10)

        #name
        nameCtrl = wx.TextCtrl(panel, -1, name)
        nameCtrl.SetInitialSize((250,-1))
        mySizer_1.Add(wx.StaticText(panel, -1, self.text.actionName), (0,0))
        mySizer_1.Add(nameCtrl, (1,0))

        #host
        hostCtrl = wx.TextCtrl(panel, -1, host)
        hostCtrl.SetInitialSize((150,-1))
        mySizer_2.Add(wx.StaticText(panel, -1, self.text.hostName), (1,0))
        mySizer_2.Add(hostCtrl, (1,1))

        #port
        portCtrl = panel.SpinIntCtrl(port)
        portCtrl.SetInitialSize((75,-1))
        mySizer_3.Add(wx.StaticText(panel, -1, self.text.portName), (1,0))
        mySizer_3.Add(portCtrl, (1,1))

        #use credentials
        ucredCtrl = wx.CheckBox(panel, -1, "")
        ucredCtrl.SetValue(ucred)
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.ucred), (1,0))
        mySizer_4.Add(ucredCtrl, (2,0))

        #user
        userCtrl = wx.TextCtrl(panel, -1, username)
        userCtrl.SetInitialSize((250,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.username), (3,0))
        mySizer_4.Add(userCtrl, (4,0))

        #password/key
        pwordCtrl = wx.TextCtrl(panel, -1, password)
        pwordCtrl.SetInitialSize((250,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.password), (5,0))
        mySizer_4.Add(pwordCtrl, (6,0))

        #use TLS/SSL
        utlsCtrl = wx.CheckBox(panel, -1, "")
        utlsCtrl.SetValue(utls)
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.utls), (7,0))
        mySizer_4.Add(utlsCtrl, (8,0))

        #path to cert
        certsCtrl = wx.TextCtrl(panel, -1, ca_certs)
        certsCtrl.SetInitialSize((400,-1))
        mySizer_4.Add(wx.StaticText(panel, -1, self.text.certs), (9,0))
        mySizer_4.Add(certsCtrl, (10,0))

        #topic
        topicCtrl = wx.TextCtrl(panel, -1, topic)
        topicCtrl.SetInitialSize((250,-1))
        mySizer_5.Add(wx.StaticText(panel, -1, self.text.topicName), (1,0))
        mySizer_5.Add(topicCtrl, (2,0))

        #file
        bfileCtrl = MyFileBrowseButton(
            panel,
            toolTip = self.text.toolTipFile,
            dialogTitle = self.text.browseFile,
            buttonText = eg.text.General.browse,
            startDirectory = eg.configDir,
            defaultFile = bfile
        )
        bfileCtrl.SetInitialSize((400,-1))
        bfileCtrl.GetTextCtrl().SetValue(bfile)
        bfileCtrl.GetTextCtrl().SetEditable(False)
        mySizer_6.Add(wx.StaticText(panel, -1, self.text.fileName), (1,0))
        mySizer_6.Add(bfileCtrl, (2,0))

        #qos
        qosCtrl = panel.SpinIntCtrl(qos, min=0, max=2)
        qosCtrl.SetInitialSize((50,-1))
        mySizer_7.Add(wx.StaticText(panel, -1, self.text.qosName), (1,0))
        mySizer_7.Add(qosCtrl, (1,1))

        #retain
        retainCtrl = wx.CheckBox(panel, -1, '')
        retainCtrl.SetValue(retain)
        retainCtrl.SetInitialSize((50,-1))
        mySizer_8.Add(wx.StaticText(panel, -1, self.text.retainName), (1,0))
        mySizer_8.Add(retainCtrl, (1,1))

        panel.sizer.Add(mySizer_1, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_2, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_3, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_4, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_5, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_6, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_7, 0, flag = wx.EXPAND)
        panel.sizer.Add(mySizer_8, 0, flag = wx.EXPAND)

        if cid == '':
            random.jumpahead(168)
            tr = random.random()
            cid = str(tr).split('.')[1]

        while panel.Affirmed():
            name = nameCtrl.GetValue()
            host = hostCtrl.GetValue()
            port = portCtrl.GetValue()
            ucred = ucredCtrl.GetValue()
            username = userCtrl.GetValue()
            password = pwordCtrl.GetValue()
            utls = utlsCtrl.GetValue()
            ca_certs = certsCtrl.GetValue()
            topic = topicCtrl.GetValue()
            bfile = bfileCtrl.GetTextCtrl().GetValue()
            qos = qosCtrl.GetValue()
            retain = retainCtrl.GetValue()
            panel.SetResult(
                name,
                host,
                port,
                topic,
                bfile,
                qos,
                retain,
                cid,
                ucred,
                username,
                password,
                utls,
                ca_certs
            )



class MyFileBrowseButton(eg.FileBrowseButton):

    def __init__(self,*args,**kwargs):
        if 'defaultFile' in kwargs:
            self.defaultFile = kwargs['defaultFile']
            del kwargs['defaultFile']
        else:
            self.defaultFile = ""
        eg.FileBrowseButton.__init__(self, *args, **kwargs)


    def GetValue(self):
        if self.textControl.GetValue():
            res = self.textControl.GetValue()
        else:
            res = "%s\\%s" % (self.startDirectory, self.defaultFile)
        return res


    def GetTextCtrl(self):          #  now I can make build-in textCtrl
        return self.textControl     #  non-editable !!!