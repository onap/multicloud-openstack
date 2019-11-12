# 1. compile hpa plugin
cd hpa
python setup.py compile

# 2. install hpa plugin
cd hpa
python setup.py install

# 3. test hpa plugin
cd hpa/test
# 3.1 test cloud extra info with dpdk
python test.py -f "dpdk"
# 3.2 test without cloud extra info
python test.py -t "windriver"
python test.py -t "starlingx"
python test.py -t "pike"
