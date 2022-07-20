#!/usr/bin/env python
# coding: UTF-8

import csv
import math
import os
import subprocess
import rospy
import rospkg
from geometry_msgs.msg import Twist

# Note. This code is for ROS melodic and python 2.7


class SpreadSheetController(object):
    def __init__(self, spread_sheet_key, outdir, command_time, linear_vel, angular_vel, topic_cmd_vel="cmd_vel"):
        self.pub_cmd_vel = rospy.Publisher(topic_cmd_vel, Twist, queue_size=10)
        self.spread_sheet_key = spread_sheet_key
        self.csv = outdir + "/robot.csv"
        self.url = "https://docs.google.com/spreadsheets/d/" + \
            self.spread_sheet_key + "/export?gid=0&format=csv"
        self.wget = "wget -O " + self.csv + " '" + self.url + "'"
        rospy.loginfo("OK I will read by " + self.wget)
        self.devnull = open(os.devnull, 'w')
        self.commands = []
        self.command_arrival = rospy.get_time()
        self.command_time = command_time
        self.twist = Twist()
        self.linear_vel = linear_vel
        self.angular_vel = angular_vel

    def __del__(self):
        self.devnull.close()

    def read_csv(self):
        try:
            data = []
            csvfile = open(self.csv, 'r')
            reader = csv.reader(csvfile)
            for row in reader:
                data.append(row[0])
            csvfile.close()
            return data
        except Exception as e:
            rospy.logerr(str(e))
            return None

    def spin(self):
        subprocess.call(
            self.wget, stdout=self.devnull, stderr=self.devnull, shell=True)
        data = self.read_csv()
        tm = rospy.get_time()
        if data is not None and (len(data) is not len(self.commands)):
            self.commands = data
            if self.commands:
                command = self.commands[-1].lower()
                rospy.loginfo("Receive new command " + command)
                self.command_arrival = tm
                self.twist = Twist()
                if command == "forward":
                    self.twist.linear.x = abs(self.linear_vel)
                elif command == "back":
                    self.twist.linear.x = -abs(self.linear_vel)
                elif command == "left":
                    self.twist.angular.z = abs(self.angular_vel)
                elif command == "right":
                    self.twist.angular.z = -abs(self.angular_vel)
                else:
                    rospy.logerr("UnKnown command " + command)
            else:
                rospy.loginfo("Command csv was cleared")
                self.twist = Twist()
        if tm - self.command_arrival > self.command_time:
            self.twist = Twist()
            rospy.loginfo("Command is expiered")
        self.pub_cmd_vel.publish(self.twist)


def main():
    script_name = os.path.basename(__file__)
    node_name = os.path.splitext(script_name)[0]
    rospy.init_node(node_name)
    spread_sheet_key = rospy.get_param("~spread_sheet_key")
    command_time = rospy.get_param("~command_time", default=3)
    linear_vel = rospy.get_param("~linear_vel", default=0.3)
    angular_vel = rospy.get_param("~angular_vel", default=math.radians(30))
    rospack = rospkg.RosPack()
    outdir = rospack.get_path('oit_remocon_google')
    if not spread_sheet_key:
        rospy.logerr("spread_sheet_key is empty")
        exit(1)
    rate = rospy.Rate(5)
    controller = SpreadSheetController(
        spread_sheet_key, outdir, command_time, linear_vel, angular_vel)
    while not rospy.is_shutdown():
        controller.spin()
        rate.sleep()


if __name__ == '__main__':
    main()
