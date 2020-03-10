#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# from ctrl.ost_status_item import OstState
#
# state = OstState.finished()
#
# if state == OstState.assigned():
#     print OstState.assigned()
# else:
#     print OstState.finished()




# from task.alert_io_task import AlertIOTask
# from task.io_task import IOTask
# from task.base_task import BaseTask
# from task.empty_task import EmptyTask
# from msg.message_factory import *


# task = AlertIOTask("mail_server",
#               "mail_sender",
#               "mail_receiver",
#               3000,
#               1000000,
#               1000000,
#               "off",
#                "target_dir_lustre_nyx",
#                "/usr/bin/lfs",
#                "yes",
#                "nyx",
#                "127.0.0.1",
#                "5557")
#
# task.ost_name = "OST0000"
# task.oss_ip = "127.0.0.1"
#
# task_assign = TaskAssign(task)
# print task_assign.to_string()
#
# message = "TASK_ASS;task.alert_io_task;AlertIOTask;OST0000;127.0.0.1;mail_server;mail_sender;mail_receiver;3000;1000000;1000000;off;target_dir_lustre_nyx;/usr/bin/lfs;yes;nyx;127.0.0.1;5557"
#
# task_assign = TaskAssign(message)
# print task_assign.to_string()
#
# header_items = task_assign.header.split(BaseMessage.field_separator)
# body_items = task_assign.body.split(BaseMessage.field_separator)
#
# in_msg_ost_name = header_items[3]
# in_msg_oss_ip = header_items[4]
#
# in_msg_block_size_bytes = body_items[0]
# in_msg_total_size_bytes = body_items[1]
# in_msg_target_dir = body_items[2]
# in_msg_lfs_bin = body_items[3]
# in_msg_lfs_target = body_items[4]
# in_msg_db_proxy_target = body_items[5]
# in_msg_db_proxy_port = body_items[6]
#
# in_raw_data = 'TASK_ASS;task.alert_io_task;AlertIOTask;OST0000;10.20.3.166;mail_server;mail_sender;mail_receiver;3000;1000000;1000000000;off;target_dir;lfs_bin;lfs;lxbk0341.gsi.de;5777'
# in_raw_data = 'ACK'
#
# task = task_assign.to_task()
#
# print task.ost_name
# print task.lfs_target
#
# task = EmptyTask()
#
# task.ost_name = "OST0000"
# task.oss_ip = "127.0.0.1"
#
# task_assign = TaskAssign(task)
#
# task_assign.to_task()





#
#
#
# if task_base_classes[0].__bases__[0].__bases__[0].__name__ == object.__name__:
#     print "XXXX"
#
# task_class = IOTask.__class__
#
# task_base_classes = task_class.__bases__
#
# for base_class in task_base_classes[0].__bases__:
#     print base_class.__name__


# from threading import Timer
#
#
# def my_func(args):
#
#     print len(args)
#     print type(args)
#
#     print args[0]
#     print args[2]
#
#
# ost_name = "OST"
# message = "message"
# subject = "subject"
#
# args = [(ost_name, message, subject)]
#
#
# t = Timer(0, my_func, args)
#
# t.start()

# t.cancel()


# import smtplib
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEBase import MIMEBase
# from email.MIMEText import MIMEText
# from email.MIMEImage import MIMEImage
#
#
# def create_mail(sender, subject, receiver, text):
#
#     mail = "From: <%s>\nTo: <%s>\nSubject: %s\n\n%s" % (sender, receiver, subject, text)
#
#     return mail
#
#
# ost_name = "OST0000"
# oss_ip = "127.0.0.1"
# alert_threshold = 1
#
# mail_server = "localhost"
# mail_sender = "hpc-data@gsi.de"
# mail_receiver = "g.iannetti@gsi.de"
# mail_subject = "Performance Degradation Detected: " + ost_name
# mail_text = "OST Name: %s\nFile Server IP: %s\nAlert Threshold: %ss" % (ost_name, oss_ip, str(alert_threshold))
#
# mail = create_mail(mail_sender, mail_subject, mail_receiver, mail_text)
#
# print mail
#
# smtp_conn = smtplib.SMTP(mail_server)
# smtp_conn.sendmail(mail_sender, mail_receiver, mail)
# smtp_conn.quit()
