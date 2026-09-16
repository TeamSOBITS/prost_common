from setuptools import find_packages, setup

package_name = 'prost_scratch'

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
    maintainer='sobit-x2',
    maintainer_email='sobit-x2@todo.todo',
    description='The prost_scratch package',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'qr_recode = prost_scratch.qr_recode:main',
            'rgb_average_value = prost_scratch.rgb_average_value:main',
            'wifi_connect = prost_scratch.wifi_connect:main',
            'wifi_connect_sim = prost_scratch.wifi_connect_sim:main',
            'tf_confirmation = prost_scratch.tf_confirmation:main',
            'color_recognition_range_drawing = prost_scratch.color_recognition_range_drawing:main',
            'scratch3_connector = prost_scratch.scratch3_connector:main',
            'prost_scratch_kobuki_controller = prost_scratch.prost_scratch_kobuki_controller:main',
        ],
    },
)
