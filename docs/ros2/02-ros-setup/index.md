---
title: 02 ROS 环境搭建
description: VMware 虚拟机、Ubuntu 24.04 与 ROS2 Jazzy 的完整安装流程
---

# 02 ROS 环境搭建

> 安装与配置。

一套可用的 ROS2 开发环境：Windows 11（主机）＋ VMware 虚拟机＋ Ubuntu 24.04（客户机）＋ ROS2 Jazzy。本章按"装虚拟机 → 装 Ubuntu → 换源 → 装 ROS2"的顺序走一遍。

## 本章地图

| 阶段                | 主题                              |
| ------------------- | --------------------------------- |
| 1 安装流程          | 为什么用 Linux、整体路线          |
| 2 虚拟机环境搭建    | VMware Workstation 安装与新建向导 |
| 3 Ubuntu 24.04 搭建 | 系统安装、换源、必备环境          |
| 4 ROS2 环境搭建     | 编码、仓库、核心库、验证          |

---

## 一、安装流程

- ROS2 的**部署环境**与**开发环境**都选择 Linux。
- 但绝大多数开发者用 Windows，所以：**在 Windows 中安装虚拟机 → 虚拟机中部署 Linux → Linux 中构建 ROS2**。
- 本课方案：**Linux on Windows**，最终得到 ROS2 Jazzy 开发环境。

![方案：Linux on Windows](./images/p004-01.webp)

技术栈从下到上依次是：

```
ROS2 Jazzy（Robotics OS）
  ↑ Ubuntu 24.04 LTS（Guest OS）
  ↑ VMware Workstation（虚拟化软件）
  ↑ Windows 11（Host OS）
```

四步走：**① 装 VMware → ② 建 Ubuntu 虚拟机 → ③ 装 Ubuntu 系统 → ④ 装 ROS2 Jazzy 与核心包**。

![技术栈与四步流程](./images/p005-02.webp)
![四步流程](./images/p005-03.webp)

---

## 二、虚拟机环境搭建

下载 VMware Workstation 安装包，双击运行安装。

![下载并安装 VMware](./images/p007-04.webp)

新建虚拟机向导的关键选择：

| 步骤         | 选择                                                         |
| ------------ | ------------------------------------------------------------ |
| 配置类型     | **自定义（高级）**                                           |
| 虚拟机名称   | `itheima_ros`，位置自选                                      |
| 安装来源     | 选择 Ubuntu 的 **ISO 镜像**（自动识别 Ubuntu 64 位 24.04.2） |
| 简易安装信息 | 全名 / 用户名 / 密码（如 itheima）                           |
| 处理器       | 按电脑配置，示例 2 处理器 × 8 核                             |
| 内存         | **至少 4GB**，示例 8192MB                                    |
| 网络类型     | **NAT**                                                      |
| I/O 控制器   | LSI Logic（推荐）                                            |
| 磁盘类型     | SCSI（推荐）                                                 |
| 磁盘         | 创建新虚拟磁盘，**30GB**，拆分成多个文件                     |
| 完成         | 勾选"创建后开启此虚拟机"                                     |

![自定义配置](./images/p008-05.webp)
![命名虚拟机](./images/p009-06.webp)
![选择 Ubuntu 镜像](./images/p009-07.webp)
![简易安装信息](./images/p010-08.webp)
![处理器配置](./images/p011-09.webp)
![内存配置](./images/p011-10.webp)
![网络类型 NAT](./images/p012-11.webp)
![I/O 控制器](./images/p012-12.webp)
![磁盘类型](./images/p013-13.webp)
![创建新虚拟磁盘](./images/p013-14.webp)
![指定磁盘容量](./images/p014-15.webp)
![指定磁盘文件](./images/p014-16.webp)
![准备创建](./images/p015-17.webp)

> [!NOTE] 侧通道缓解提示
> 出现"启用了侧通道缓解"的提示，直接「确定」即可。

![侧通道缓解提示](./images/p015-18.webp)

---

## 三、Ubuntu 24.04 环境搭建

### 3.1 系统安装向导

依次选择：**语言（中文简体）→ 可访问性（跳过）→ 键盘布局（汉语）→ 连接到互联网（有线）→ 更新（跳过）→ 安装 Ubuntu → 交互安装 → 默认集合 → 不装专有软件 → 擦除磁盘并安装 → 设置账户 → 时区（Shanghai）→ 安装 → 立即重启**。

![选择语言](./images/p017-19.webp)
![键盘布局](./images/p018-21.webp)
![连接到互联网](./images/p018-22.webp)
![跳过更新](./images/p019-23.webp)
![安装 Ubuntu](./images/p019-24.webp)
![交互安装](./images/p020-25.webp)
![应用程序默认集合](./images/p020-26.webp)
![安装专有软件](./images/p021-27.webp)
![擦除磁盘并安装](./images/p021-28.webp)
![设置账户](./images/p022-29.webp)
![选择时区](./images/p022-30.webp)
![准备安装](./images/p023-31.webp)
![安装完成](./images/p024-33.webp)

> [!TIP] 安装完成后
> 若重启时出现 `VMware Workstation 不可恢复错误 (vcpu-12)`，这是虚拟机常见问题，重启 VMware 或调整虚拟化设置即可。

![VMware 报错示例](./images/p024-34.webp)

### 3.2 修改软件源（换阿里源）

打开「**软件和更新**」→ 在「Ubuntu 软件」页的「下载自」选择「**其它…**」→ 展开「中国」，选择 `mirrors.aliyun.com` → 选择服务器 → 提示列表过时时点「重新载入」。

![打开软件和更新](./images/p025-35.webp)
![下载自 其它](./images/p025-36.webp)
![选择阿里云](./images/p025-37.webp)
![重新载入](./images/p025-38.webp)

### 3.3 必备环境

```bash
# 系统更新
sudo apt update
sudo apt upgrade

# 安装 OpenSSH（方便远程连接）
sudo apt install openssh-server
sudo service ssh restart
sudo systemctl enable ssh

# 解决虚拟机无法全屏
sudo apt install open-vm-tools-desktop
sudo reboot
```

---

## 四、ROS2 环境搭建

### 4.1 编码检测

先确认是 UTF-8 环境：

```bash
locale
```

若不是，则执行：

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 4.2 安装必备仓库与 apt source

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
```

再安装 ROS2 的 apt source（把 `.deb` 附件拷到 Ubuntu 目录）：

```bash
sudo chmod 777 ros2-apt-source_1.1.0.noble_all.deb
sudo dpkg -i ros2-apt-source_1.1.0.noble_all.deb
```

### 4.3 安装 ROS 必备环境与核心库

```bash
sudo apt update
sudo apt upgrade
sudo apt install tar bzip2 wget -y
sudo apt install ros-dev-tools -y

# ROS 核心库（Jazzy 桌面版）
sudo apt install ros-jazzy-desktop -y

# 环境变量配置
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
source ~/.bashrc
```

### 4.4 验证安装

```bash
ros2 run turtlesim turtlesim_node
```

出现小海龟窗口，就说明 ROS2 安装成功。

![小海龟窗口，安装成功](./images/p031-39.webp)

---

## 本章小结

- **路线**：Windows → VMware → Ubuntu 24.04 → ROS2 Jazzy。
- **虚拟机**：自定义配置、NAT 网络、≥4GB 内存、30GB 磁盘。
- **Ubuntu**：交互安装 + 擦除磁盘 + 设置账户，装完换阿里源。
- **必备环境**：`apt update/upgrade`、OpenSSH、`open-vm-tools-desktop`。
- **ROS2**：配好 apt source，装 `ros-jazzy-desktop`，用 turtlesim 验证。

> [!CAUTION] 最容易踩的坑
> 忘记 `source /opt/ros/jazzy/setup.bash`，导致 `ros2` 命令找不到。
