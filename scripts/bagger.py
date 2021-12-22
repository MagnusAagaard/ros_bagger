#!/usr/bin/python3
import rospy
import rosbag
import rostopic
import sys
from people_msgs.msg import PositionMeasurementArray
from std_msgs.msg import Time
from threading import Lock
from datetime import datetime
from pathlib import Path

class Bagger:
    def __init__(self):
        self.__init_params()
        self.time_since_last_trigger_msg = rospy.Time.now() - rospy.Duration(self.trigger_timeout+1)
        self.lock = Lock()
        self.lock.acquire()
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.bag = rosbag.Bag(f'{Path.home()}/{now}.bag', 'w')
        self.lock.release()
        self.time_delay = -1
        self.__init_subscribers()

    def __del__(self):
        rospy.loginfo("Shutting down bagger")
        self.lock.acquire()
        self.bag.close()
        self.lock.release()
        rospy.loginfo("Shut down bagger")

    def __init_params(self):
        self.topics = rospy.get_param('~topics','')
        if not self.topics:
            rospy.logerr('No topics provided on parameter \'~topics\'. Exiting..')
            sys.exit(-1)
        self.trigger_timeout = rospy.get_param('~trigger_timeout', 30)
        self.trigger_topic = rospy.get_param('~trigger_topic','')
        if not self.trigger_topic:
            rospy.logerr('Topic \'trigger_topic\' was not provided. Exiting..')
            sys.exit(-1)
        self.topic_when_triggered = rospy.get_param('~topic_when_triggered','')
        if not self.topic_when_triggered:
            rospy.logerr('Topic \'topic_when_triggered\' was not provided. Exiting..')
            sys.exit(-1)

    def __init_subscribers(self):
        trigger_class, _, _ = rostopic.get_topic_class('/{}'.format(self.trigger_topic), blocking=True)
        rospy.Subscriber(self.trigger_topic, trigger_class, self.__trigger_cb, queue_size=None)
        topic_when_triggered_class, _, _ = rostopic.get_topic_class('/{}'.format(self.topic_when_triggered), blocking=True)
        rospy.Subscriber(self.topic_when_triggered, topic_when_triggered_class, self.__topic_when_triggered_cb, queue_size=None)
        for topic in self.topics:
            topic_class, _, _ = rostopic.get_topic_class('/{}'.format(topic), blocking=True)
            rospy.loginfo(f'Subscribing to topic \'{topic}\' with class \'{topic_class}\'..')
            rospy.Subscriber(topic, topic_class, callback=self.__callback_creator(topic), queue_size=None)
        
    def __trigger_cb(self, msg):
        self.time_since_last_trigger_msg = rospy.Time.now()

    def __topic_when_triggered_cb(self, msg):
        if (rospy.Time.now() - self.time_since_last_trigger_msg) < rospy.Duration(self.trigger_timeout):
            self.lock.acquire()
            self.bag.write(self.topic_when_triggered, msg)
            self.lock.release()

    def __callback_creator(self, topic):
        def callback(msg):
            self.lock.acquire()
            self.bag.write(topic, msg)
            self.lock.release()
            if self.time_delay == -1:
                try:
                    time = msg.header.stamp
                    now = rospy.Time.now()
                    rospy.loginfo('Delay: {}'.format(now.to_sec()-time.to_sec()))
                    self.time_delay = now-time
                    self.lock.acquire()
                    self.bag.write('time_delay', Time(data=now-time))
                    self.lock.release()
                except Exception:
                    print('Exception in time delay calculation')
        return callback

def main():
    rospy.init_node('ros_bagger', log_level=rospy.INFO)
    bagger = Bagger()
    rospy.spin()

if __name__ == "__main__":
    main()
