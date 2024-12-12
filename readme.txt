https://github.com/L4STeam/linux
To install the kernel  modules (debian derivatives):

wget https://github.com/L4STeam/linux/releases/download/testing-build/l4s-testing.zip
unzip l4s-testing.zip
sudo dpkg --install debian_build/*
sudo update-grub  # This should auto-detect the new kernel
# You can optionally set newly installed kernel as the default, e.g., editing GRUB_DEFAULT in /etc/default/grub
# You can now reboot (and may have to manually select the kernel in grub)

# Be sure that the newly installed kernel is successfully used, e.g., checking output of
uname -r

# Be sure to ensure the required modules are loaded before doing experiments, e.g.,
sudo modprobe sch_dualpi2
sudo modprobe tcp_prague
