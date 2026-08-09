# Copy a Shape Key / 复制形态键

**English:** Select the shape key you want to copy on a mesh object, go to the
**Scripting** workspace, paste the script below into the Text Editor and press
**Run Script**. A new shape key named `<name>_copy` will be created with the same
vertex offsets (`numpy` is bundled with Blender, no extra install needed).

**中文：** 在网格对象上选中要复制的形态键，切换到 **Scripting** 工作区，
把下面的脚本粘贴到文本编辑器中并点击**运行脚本**。脚本会生成一个名为
`<名称>_copy`、顶点偏移相同的新形态键（`numpy` 由 Blender 自带，无需额外安装）。

```python
import bpy
import numpy as np


def duplicate_active_shape_key():
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH' or not obj.data.shape_keys:
        raise Exception("Select a mesh object with shape keys. / 请选择带有形态键的网格对象。")

    shape_keys = obj.data.shape_keys.key_blocks
    active_index = obj.active_shape_key_index
    if not 0 <= active_index < len(shape_keys):
        raise Exception("Invalid active shape key index. / 活动形态键索引无效。")

    src_key = shape_keys[active_index]
    new_key = obj.shape_key_add(name=f"{src_key.name}_copy", from_mix=False)
    new_key.value = src_key.value

    src_data = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    src_key.data.foreach_get("co", src_data)
    new_key.data.foreach_set("co", src_data)

    obj.active_shape_key_index = len(shape_keys) - 1
    bpy.context.view_layer.update()


if __name__ == "__main__":
    try:
        duplicate_active_shape_key()
        print("Shape key copied successfully! / 形态键复制成功！")
    except Exception as e:
        print(f"Error / 错误：{e}")
```
