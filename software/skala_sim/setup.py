from pathlib import Path
from setuptools import setup

package_name = 'skala_sim'
data = [('share/ament_index/resource_index/packages', ['resource/skala_sim']),
        ('share/skala_sim', ['package.xml'])]
for directory in ('launch', 'config', 'models', 'worlds', 'web'):
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file():
            data.append(('share/skala_sim/'+str(path.parent), [str(path)]))

setup(name=package_name, version='0.1.0', packages=[package_name], data_files=data,
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Skala project', maintainer_email='skala@example.invalid',
      description='Skala fixed-track Gazebo simulation', license='LicenseRef-Unspecified',
      entry_points={'console_scripts': [
          'command_guard = skala_sim.command_guard:main',
          'validate = skala_sim.validate:main',
          'demo = skala_sim.demo:main',
          'web_teleop = skala_sim.web_teleop:main',
          'recorder = skala_sim.recorder:main',
      ]})
