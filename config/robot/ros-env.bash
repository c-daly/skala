# Source in Bash before starting native robot nodes or ROS inspection commands.
source /opt/ros/jazzy/setup.bash
if [[ -f "$HOME/skala_ws/install/setup.bash" ]]; then
  source "$HOME/skala_ws/install/setup.bash"
fi
export ROS_DOMAIN_ID=31
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_STATIC_PEERS=''
unset ROS_LOCALHOST_ONLY ROS_DISCOVERY_SERVER
