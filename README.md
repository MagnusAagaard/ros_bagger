# ros_bagger
This node creates a rosbag, subscribing to the topics specified in the launch file. A trigger topic can be defined to trigger an aditional topic to subscribe to whenever data is coming in on the trigger topic. If no data is coming in on the trigger topic, a timeout is specified to stop recording data after the timeout has run out.
