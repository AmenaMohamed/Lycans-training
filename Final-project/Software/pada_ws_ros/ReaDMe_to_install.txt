
git clone https://github.com/Lycans-Training-27/Team--04-PADA.git

cd Team--04-PADA

git checkout final-project-pada-design

cd electrical/Software/pada_ws_ros

colcon build --symlink-install

source install/setup.bash

echo "source ~/Team--04-PADA/electrical/Software/pada_ws_ros/install/setup.bash" >> ~/.bashrc

cd Team--04-PADA/electrical/Software/pada_ws_ros

rosdep install --from-paths src --ignore-src -r -y
#to install all packages deps 
