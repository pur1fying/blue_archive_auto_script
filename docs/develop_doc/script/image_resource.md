# 图像资源管理
::: info
阅读这部分内容前你可能需要了解
1. 图像被加载到内存后的数据结构, 如何访问每一处的像素值
2. 基础的python-opencv的函数使用

   | 函数名称                    | 作用       |
   |-------------------------|----------|
   | `cv2.imread`            | 读取图像     |
   | `cv2.imwrite`           | 保存图像     |
   | `cv2.resize`            | 裁剪图像     |
   | `cv2.cvtColor`          | 转换图像颜色空间 |
   | **`cv2.matchTemplate`** | 模板匹配     |
:::


## 图像资源读取
对应文件路径 : `"core/position.py"`

规则:
1. 图像具有 server, prefix, name 和 position, 这些信息存储在 `src/images/server/x_y_range/*.py` 文件中。
   
   | 变量名        | 含义                                       | 是否必要 |
   |------------|------------------------------------------|------|
   | `server`   | 服务器                                      | 是    |
   | `path`     | 图像路径                                     | 是    |
   | `prefix`   | 图像所属任务类别                                 | 是    |
   | `name`     | 图像名称                                     | 是    |
   | `position` | 图像截取时坐标 <br/>(x1, y1, x2, y2)<br/>左上, 右下 | 否    |
   
   - note: 你也许会疑惑为什么大部分x_y_range.py中`prefix`和`path`相同, 请注意`x_y_range/activity`中的x_y_range.py, 每一期活动需要从不同的`path`加载图像, 但是他们在`prefix`都是`activity`
      - 即
         1. `path`仅与图像加载有关
         2. `prefix`仅与图像的引用有关
2. 图像的真实路径为 
   ```python 
    path = f"src/images/{server}/{path}/{name}.png"
   ```
3. 图像被加载到内存后，存储在 `core.position.image_dic` 中

   - 获取图像
      ```python
      template = image_dic[server][f"{prefix}_"{name}"] 
      ```
      
4. 图像的位置信息被储存在 `core.position.image_x_y_range` 中
   获取图像区域:
   - 方法一
   ```python
    area = image_x_y_range[server][prefix][name]
   ```
   - 方法二
    ```python
    area = get_area(server, f"{prefix}_{name}")
    ```
5. 图像的 prefix 可以包含 `"_"` 字符，但 name 不能包含。  
   原因: [`get_area`](#get_area) 使用 `rsplit` 方法分割`prefix`和`name`, 因此 name 不能包含 `"_"`, 一般用`"-"`分割。

例:
- `src/images/CN/x_y_range/arena.py`, 该路径表示服务器是**国服(CN)**
   
```python
prefix = "arena"    # 图像用于竞技场任务
path = "arena"      # 存放在 "src/images/CN/arena" 目录下
x_y_range = {
    'menu': (107, 9, 162, 36),    # 图像"src/images/CN/arena/menu.png"截取时的坐标
    'edit-force': (107, 9, 162, 36)
}
```
   
剪切后的截图图像放入 `resource/images/server/arena` 目录下：

```shell
resource/images/server/arena
│
├── menu.png
└── edit-force.png
```
    
## 相关函数

###  `init_image_data`
- **Args**:
  1. `self`: [**Baas_thread**](/develop_doc/script/Baas_thread) 的实例, 用于提供`server` / `current_game_activity`等信息
- **description**:  根据`self.server`, 初始化**一个服务器**的所有图像数据
- **note**:
  1. 该函数扫描`src/image/server/x_y_range`目录下的所有文件, 根据上文[图像资源读取](#图像资源读取)规则初始化图像数据
  2. 每一期活动的图像单独加载, 根据当期活动(`self.current_game_activity`)名称加载对应图像
### `get_area`
- **Args**:
   1. `server`
   2. `name`
- **description**:  获取指定图像的区域
- **note**: 参数中的`name`与上文中的`name`不同, 这里的`name`是`prefix_name`的形式。
- **return**: `(x1, y1, x2, y2)`
- 例:
   ```python
   area = get_area("CN", "arena_menu") # (107, 9, 162, 36)
   ```