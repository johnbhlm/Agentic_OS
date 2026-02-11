from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'assistant_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools',
                      # Python 依赖列表
                    'openai',
                    'pyaudio',
                ],
    zip_safe=True,
    maintainer='maintenance',
    maintainer_email='john_bh@163.com',
    description='Assistant robot with speech interface, planning and action execution.',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 这里注册你的主程序入口
            'main = assistant_robot.main:main',
            'fake_vla_node = assistant_robot.execution.fake_vla_node:main',
            'fake_vln_node = assistant_robot.execution.fake_vln_node:main',
        ],
    },
)
