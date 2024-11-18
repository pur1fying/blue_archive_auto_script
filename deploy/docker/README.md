### How to Use Docker

> This project aims to support Docker deployment, but currently, the Docker deployment is not functioning properly. If you have a solution, please submit a PR.

1. Ensure Docker is installed on your computer, and clone this project to your local machine.
2. Navigate to the project directory, copy this folder to the project root, and build the image:
    ```shell
    docker build -t baas:v1.0 .
    ```
3. Method 1 for running the container: using `docker run`
    ```shell
    docker run -it -v "$PWD:/app" -p 5900:5900 baas:v1.0
    ```
4. Method 2 for running the container: using `docker-compose`
    ```shell
    docker-compose up -d
    ```
5. You can connect to the GUI via VNC Viewer, with the default port set to 5900.
6. Additionally, if your system supports display, you can modify the instructions in `entrypoint.sh` to run it directly on your local machine.
