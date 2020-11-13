import rospy
import os
from std_msgs.msg import String,Int16
from ros_actor_cmd_pose_plugin_msgs.msg import ActorInfo
from gazebo_msgs.srv import DeleteModel,GetModelState
import time

actor_num = 6
err_threshold = 1
coordx_bias = 3
coordy_bias = 9
actor_id_dict = {'green':[0], 'blue':[1], 'brown':[2], 'white':[3], 'red':[4,5]}

def actor_info_callback(msg):
    global target_finish, start_time, score, count_flag, left_actors, actors_pos, find_time
    actor_id = actor_id_dict[msg.cls]
    if msg.cls == 'red':
        red_cnt = 0
    for i in actor_id:
        if i not in left_actors:
            break
        if (msg.x-actors_pos[i].x)**2+(msg.y-actors_pos[i].y)**2<err_threshold**2:
            if not count_flag[i]:
                count_flag[i] = True
                find_time[i] = rospy.get_time()
                print("find actor_"+str(i))
            elif rospy.get_time() - find_time[i] >= 15:
                target_finish += 1
                del_model('actor_'+str(i))
                left_actors.remove(i)
                time_usage = rospy.get_time() - start_time
                print('actor_'+str(i)+' is OK')
                print('Time usage:', time_usage)

                # calculate score
                if target_finish == 6:
                    score = (800 - time_usage) - sensor_cost * 3e-3
                    print('score:',score)
                    print("Mission finished")
                    os._exit(0)
                else:
                    score = (1 + target_finish) * 1e2 - sensor_cost * 3e-3
                    print('score:',score)              
        else:
            if msg.cls == 'red':
                red_cnt += 1
                if red_cnt == 2:
                    count_flag[i] = False
            else:
                count_flag[i] = False

if __name__ == "__main__":
    left_actors = range(actor_num)
    actors_pos = [None] * actor_num
    count_flag = [False] * actor_num
    find_time = [0.0] * actor_num
    rospy.init_node('score_cal')
    del_model = rospy.ServiceProxy("/gazebo/delete_model",DeleteModel)
    get_model_state = rospy.ServiceProxy("/gazebo/get_model_state",GetModelState) 

    score_pub = rospy.Publisher("score",Int16,queue_size=2)  
    left_actors_pub = rospy.Publisher("left_actors",String,queue_size=2)
    actor_blue_sub = rospy.Subscriber("/actor_blue_info",ActorInfo,actor_info_callback)
    actor_green_sub = rospy.Subscriber("/actor_green_info",ActorInfo,actor_info_callback)
    actor_white_sub = rospy.Subscriber("/actor_white_info",ActorInfo,actor_info_callback)
    actor_brown_sub = rospy.Subscriber("/actor_brown_info",ActorInfo,actor_info_callback)
    actor_red1_sub = rospy.Subscriber("/actor_red1_info",ActorInfo,actor_info_callback)
    actor_red2_sub = rospy.Subscriber("/actor_red2_info",ActorInfo,actor_info_callback)

    # sensor cost
    mono_cam = 1
    stereo_cam =0
    laser1d = 0
    laser2d = 0
    laser3d = 0
    gimbal = 1
    sensor_cost = mono_cam * 5e2 + stereo_cam * 1e3 + laser1d * 2e2+ laser2d * 5e3 + laser3d * 2e4 + gimbal * 2e2
    
    target_finish = 0
    score = (1 + target_finish) * 2e2 - sensor_cost * 3e-3
    time.sleep(1)
    rate = rospy.Rate(10)
    start_time = rospy.get_time()

    while not rospy.is_shutdown():
        for i in left_actors:
            actors_pos[i] = get_model_state('actor_' + str(i), 'ground_plane').pose.position
        score_pub.publish(score)
        left_actors_pub.publish(str(left_actors))
        rate.sleep()


