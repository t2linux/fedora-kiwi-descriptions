bootloader --append-line="zswap.enabled=1" \
           --append-line="zswap.compressor=zstd" \
           --append-line="zswap.maxPoolPercent=30"
           --append-line="zswap.accept_threshold_percent=90"

%post --erroronfail
# ensure no zram
dnf remove -y zram-generator-defaults zram-generator
: > /etc/systemd/zram-generator.conf

# Create a Btrfs-compatible swapfile inside the /swap subvolume
btrfs filesystem mkswapfile --size 32g /swap/swapfile

# Enable it on boot
echo "/swap/swapfile none swap defaults 0 0" >> /etc/fstab
%end
