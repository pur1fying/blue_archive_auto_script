# 开发过程中的约定

## 关于 `.gitignore`

- **不在项目根目录下设置 `.gitignore` 文件。**
- 每位开发者应设置自己的 `.git/info/exclude` 文件，用于忽略与其开发环境相关的文件。

### 原因
- **根目录下的 `.gitignore` 文件：**  
  会影响到其他开发者的工作环境。  
- **`.git/info/exclude` 文件：**  
  仅在当前开发者的本地环境生效，确保每位开发者的忽略设置独立、互不干扰。

**你可以参考下面的`.gitignore`**

```.gitignore
/*

!cli.example.py
!service.example.py
!src
!module
!gui
!docs
!core
!deploy
!device_operation
!develop_tools

!.editorconfig
!.gitignore
!LICENSE
!README.md

!main.py
!requirements.txt
!window.py
!requirements-i18n.txt
!requirements-linux.txt
*.pyc
*.xml
