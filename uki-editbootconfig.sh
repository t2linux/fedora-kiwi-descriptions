#!/bin/sh
echo "###" "$0" "$@"

# set arch-specific variables
case "$(uname -m)" in
    aarch64) arch="aa64";    ARCH="AA64";;
    riscv64) arch="riscv64"; ARCH="RISCV64";;
    x86_64)  arch="x64";     ARCH="X64";;
esac

# figure where shim.efi and BOOT.CSV are located
shim="$(ls boot/efi/EFI/*/shim${arch}.efi)"
csv="${shim%/*}/BOOT${ARCH}.CSV"

# copy UKI images (typically one) to ${ESP}/EFI/Linux and
# generate BOOT.CSV with one entry per UKI.
echo "# csv: $csv"
echo -ne '\xff\xfe' > "$csv"
for uki in lib/modules/*/vmlinuz*.efi; do
    echo "# uki: $uki"
    ver=${uki#lib/modules/}
    ver=${ver%/*}
    mkdir -p boot/efi/EFI/Linux
    cp --reflink=auto $uki boot/efi/EFI/Linux/${ver}.efi
    echo "shim${arch}.efi,$ver,\\EFI\\Linux\\${ver}.efi ,Comment" \
        | iconv -f utf-8 -t ucs-2le >> "$csv"
done

# bz2240989: shim has a hard dependency on grub.  grub has a hard
# dependency on dracut.  Ideally we would simply not install
# grub+dracut, but given we can't until the shim bug is fixed disable
# their kernel-install plugins instead.
echo "# hack: kernel-install - disable plugins"
touch etc/kernel/install.d/20-grub.install
touch etc/kernel/install.d/50-dracut.install

# package install ran kernel-install scripts, cleanup the leftovers.
echo "# hack: kernel-install - cleanup leftovers"
rm -v boot/initramfs*
rm -v boot/EFI/Linux/*
