# Use the official Debian image as the base
FROM hub.atomgit.com/amd64/debian:latest

# Remove the original mirror
RUN rm -rf /etc/apt/sources.list.d

# Alter the source to tsinghua mirror
RUN echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware\ndeb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware\ndeb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware\ndeb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" > /etc/apt/sources.list

# Install Git Env
RUN apt-get update && apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget && apt-get install -y git

# Install Python Environment
RUN wget https://mirrors.aliyun.com/python-release/source/Python-3.9.18.tar.xz
RUN tar -xvJf Python-3.9.18.tar.xz
RUN cd Python-3.9.18 && ./configure --enable-optimizations
RUN cd Python-3.9.18 && make -j $(nproc) && make altinstall
RUN rm -rf Python-3.9.18.tar.xz Python-3.9.18


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Copy the rest of the application code to the container
COPY . .

# Set the command to run the application
CMD ["bash", "entrypoint.sh"]
