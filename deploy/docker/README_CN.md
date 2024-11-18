
### Docker 使用方法
> 本项目拟支持Docker部署，但目前Docker部署仍无法正常运行，如有解决方案，请提交PR
1. 确保你的电脑中存在Docker, 先clone本项目到本地
2. 进入项目目录，先将本文件夹复制到项目根目录，构建镜像：
    ```shell
    docker build -t baas:v1.0 .
    ```
3. 运行容器方法一：使用docker run
    ```shell
    docker run -it -v "$PWD:/app" -p 5900:5900 baas:v1.0
    ```
4. 运行容器方法二：使用docker-compose
    ```shell
    docker-compose up -d
    ```
5. 可以通过VNC Viewer连接到GUI画面，端口默认为5900
6. 同时如果你的系统支持显示，可以通过修改`entrypoint.sh`中指示的内容，直接在本地运行。
