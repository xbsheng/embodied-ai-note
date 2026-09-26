from setuptools import find_packages, setup

package_name = 'AI_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='itheima',
    maintainer_email='itheima@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mcp_server_node = AI_pkg.mcp_server_node:main',
            'llm_agent_node = AI_pkg.llm_agent_node:main'
        ],
    },
)
