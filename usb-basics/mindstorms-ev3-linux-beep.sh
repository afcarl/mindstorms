# the trouble is, how to detectthe right hidraw device
DEVICE=/dev/hidraw1
echo -en \
    '\x0F\x00\x01\x00\x80\x00\x00\x94\x01\x81\x02\x82\xE8\x03\x82\xE8\x03' \
    > $DEVICE
