# Jazzy/Noble stays independent of the workstation's WSL distribution.
ARG ROS_IMAGE=ros:jazzy-ros-base-noble@sha256:5147d3ae250ce754afd399f6bfec15b33dd4e473ca357e30432a3182031bfad6
FROM ${ROS_IMAGE}

ARG LOCAL_UID=1000
ARG LOCAL_GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-jazzy-demo-nodes-cpp \
      ros-jazzy-demo-nodes-py \
      ros-jazzy-rviz2 \
      ros-jazzy-rosbag2 \
      ros-jazzy-rosbag2-storage-default-plugins \
    && rm -rf /var/lib/apt/lists/*

# Reuse an existing numeric identity (Ubuntu ships UID 1000) when present.
RUN set -eu; \
    if ! getent group "${LOCAL_GID}" >/dev/null; then groupadd -g "${LOCAL_GID}" ros; fi; \
    existing_account="$(getent passwd "${LOCAL_UID}" | cut -d: -f1)"; \
    if [ -n "${existing_account}" ]; then \
      test "${LOCAL_UID}" != 0; \
      usermod -l ros -d /home/ros -m "${existing_account}"; \
      usermod -g "${LOCAL_GID}" -s /bin/bash ros; \
    else \
      useradd -m -u "${LOCAL_UID}" -g "${LOCAL_GID}" -s /bin/bash ros; \
    fi; \
    mkdir -p /home/ros/ws/src /home/ros/bags; \
    printf '\nsource /opt/ros/jazzy/setup.bash\nif [ -f /home/ros/ws/install/setup.bash ]; then source /home/ros/ws/install/setup.bash; fi\n' >> /home/ros/.bashrc; \
    chown -R "${LOCAL_UID}:${LOCAL_GID}" /home/ros

COPY smoke.py /usr/local/lib/skala-ros/smoke.py
ENV HOME=/home/ros
USER ros
WORKDIR /home/ros/ws
# Retain the upstream /ros_entrypoint.sh, which sources the ROS environment.
CMD ["sleep", "infinity"]
