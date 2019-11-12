import traceback
import uuid
import json
import logging
from hpa import base


def ignore_case_get(args, key, def_val=""):
    if not key:
        return def_val
    if key in args:
        return args[key]
    for old_key in args:
        if old_key.upper() == key.upper():
            return args[old_key]
    return def_val

class HPA_Discovery(base.HPA_DiscoveryBase):
    """HPA Discovery implementation.
    """
    def __init__(self):
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger("hpa_discovery")
            self.fh = logging.FileHandler('discovery.log')
            self.fh.setLevel(logging.INFO)
            self._logger.addHandler(self.fh)

    def get_hpa_capabilities(self, data):
        hpa_caps = []

        # Basic capabilties
        caps_dict = self._get_hpa_basic_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("basic_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # cpupining capabilities
        caps_dict = self._get_cpupining_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("cpupining_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # cputopology capabilities
        caps_dict = self._get_cputopology_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("cputopology_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # hugepages capabilities
        caps_dict = self._get_hugepages_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("hugepages_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # numa capabilities
        caps_dict = self._get_numa_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("numa_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # storage capabilities
        caps_dict = self._get_storage_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("storage_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # CPU instruction set extension capabilities
        caps_dict = self._get_instruction_set_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("instruction_set_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # PCI passthrough capabilities
        caps_dict = self._get_pci_passthrough_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("pci_passthrough_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # SRIOV-NIC capabilities
        caps_dict = self._get_sriov_nic_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("sriov_nic_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # ovsdpdk capabilities
        caps_dict = self._get_ovsdpdk_capabilities(data)
        if len(caps_dict) > 0:
            self._logger.debug("ovsdpdk_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # self._logger.error("hpa_caps: %s" % (hpa_caps))
        return hpa_caps

    def _get_hpa_basic_capabilities(self, data):
        basic_capability = {}
        feature_uuid = uuid.uuid4()
        flavor = data["flavor"]

        try:
            basic_capability['hpa-capability-id'] = str(feature_uuid)
            basic_capability['hpa-feature'] = 'basicCapabilities'
            basic_capability['architecture'] = 'generic'
            basic_capability['hpa-version'] = 'v1'

            basic_capability['hpa-feature-attributes'] = []
            basic_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'numVirtualCpu',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\"}}'.format(flavor['vcpus'])
                 })
            basic_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key':'virtualMemSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['ram'],"MB")
                 })
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

        return basic_capability

    def _get_cpupining_capabilities(self, data):
        cpupining_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'hw:cpu_policy' in extra_specs\
                    or 'hw:cpu_thread_policy' in extra_specs:
                cpupining_capability['hpa-capability-id'] = str(feature_uuid)
                cpupining_capability['hpa-feature'] = 'cpuPinning'
                cpupining_capability['architecture'] = 'generic'
                cpupining_capability['hpa-version'] = 'v1'

                cpupining_capability['hpa-feature-attributes'] = []
                if 'hw:cpu_thread_policy' in extra_specs:
                    cpupining_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'logicalCpuThreadPinningPolicy',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(
                                 extra_specs['hw:cpu_thread_policy'])
                         })
                if 'hw:cpu_policy' in extra_specs:
                    cpupining_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key':'logicalCpuPinningPolicy',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(
                                 extra_specs['hw:cpu_policy'])
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return cpupining_capability

    def _get_cputopology_capabilities(self, data):
        cputopology_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'hw:cpu_sockets' in extra_specs\
                    or 'hw:cpu_cores' in extra_specs\
                    or 'hw:cpu_threads' in extra_specs:
                cputopology_capability['hpa-capability-id'] = str(feature_uuid)
                cputopology_capability['hpa-feature'] = 'cpuTopology'
                cputopology_capability['architecture'] = 'generic'
                cputopology_capability['hpa-version'] = 'v1'

                cputopology_capability['hpa-feature-attributes'] = []
                if 'hw:cpu_sockets' in extra_specs:
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuSockets',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_sockets'])
                         })
                if 'hw:cpu_cores' in extra_specs:
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuCores',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_cores'])
                         })
                if 'hw:cpu_threads' in extra_specs:
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuThreads',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_threads'])
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return cputopology_capability

    def _get_hugepages_capabilities(self, data):
        hugepages_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'hw:mem_page_size' in extra_specs:
                hugepages_capability['hpa-capability-id'] = str(feature_uuid)
                hugepages_capability['hpa-feature'] = 'hugePages'
                hugepages_capability['architecture'] = 'generic'
                hugepages_capability['hpa-version'] = 'v1'

                hugepages_capability['hpa-feature-attributes'] = []
                if extra_specs['hw:mem_page_size'] == 'large':
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(2,"MB")
                         })
                elif extra_specs['hw:mem_page_size'] == 'small':
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(4,"KB")
                         })
                elif extra_specs['hw:mem_page_size'] == 'any':
                    self._logger.info("Currently HPA feature memoryPageSize did not support 'any' page!!")
                else :
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs['hw:mem_page_size'],"KB")
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return hugepages_capability

    def _get_numa_capabilities(self, data):
        numa_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'hw:numa_nodes' in extra_specs:
                numa_capability['hpa-capability-id'] = str(feature_uuid)
                numa_capability['hpa-feature'] = 'numa'
                numa_capability['architecture'] = 'generic'
                numa_capability['hpa-version'] = 'v1'

                numa_capability['hpa-feature-attributes'] = []
                numa_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'numaNodes',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:numa_nodes'] or 0)
                     })

                for num in range(0, int(extra_specs['hw:numa_nodes'])):
                    numa_cpu_node = "hw:numa_cpus.%s" % num
                    numa_mem_node = "hw:numa_mem.%s" % num
                    numacpu_key = "numaCpu-%s" % num
                    numamem_key = "numaMem-%s" % num

                    if numa_cpu_node in extra_specs and numa_mem_node in extra_specs:
                        numa_capability['hpa-feature-attributes'].append(
                            {'hpa-attribute-key': numacpu_key,
                             'hpa-attribute-value':
                                 '{{\"value\":\"{0}\"}}'.format(extra_specs[numa_cpu_node])
                             })
                        numa_capability['hpa-feature-attributes'].append(
                            {'hpa-attribute-key': numamem_key,
                             'hpa-attribute-value':
                                 '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs[numa_mem_node],"MB")
                             })
        except Exception:
            self._logger.error(traceback.format_exc())

        return numa_capability

    def _get_storage_capabilities(self, data):
        storage_capability = {}
        feature_uuid = uuid.uuid4()
        flavor = data["flavor"]

        try:
            storage_capability['hpa-capability-id'] = str(feature_uuid)
            storage_capability['hpa-feature'] = 'localStorage'
            storage_capability['architecture'] = 'generic'
            storage_capability['hpa-version'] = 'v1'

            storage_capability['hpa-feature-attributes'] = []
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'diskSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['disk'] or 0, "GB")
                 })
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'swapMemSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['swap'] or 0, "MB")
                 })
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'ephemeralDiskSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['OS-FLV-EXT-DATA:ephemeral'] or 0, "GB")
                 })
        except Exception:
            self._logger.error(traceback.format_exc())

        return storage_capability

    def _get_instruction_set_capabilities(self, data):
        instruction_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'hw:capabilities:cpu_info:features' in extra_specs:
                instruction_capability['hpa-capability-id'] = str(feature_uuid)
                instruction_capability['hpa-feature'] = 'instructionSetExtensions'
                instruction_capability['architecture'] = 'Intel64'
                instruction_capability['hpa-version'] = 'v1'

                instruction_capability['hpa-feature-attributes'] = []
                instruction_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'instructionSetExtensions',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(
                             extra_specs['hw:capabilities:cpu_info:features'])
                     })
        except Exception:
            self._logger.error(traceback.format_exc())

        return instruction_capability

    def _get_pci_passthrough_capabilities(self, data):
        pci_passthrough_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:

            if 'pci_passthrough:alias' in extra_specs:
                value1 = extra_specs['pci_passthrough:alias'].split(':')
                value2 = value1[0].split('-')

                pci_passthrough_capability['hpa-capability-id'] = str(feature_uuid)
                pci_passthrough_capability['hpa-feature'] = 'pciePassthrough'
                pci_passthrough_capability['architecture'] = str(value2[2])
                pci_passthrough_capability['hpa-version'] = 'v1'


                pci_passthrough_capability['hpa-feature-attributes'] = []
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciCount',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value1[1])
                     })
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciVendorId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[3])
                     })
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciDeviceId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[4])
                                                                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return pci_passthrough_capability

    def _get_sriov_nic_capabilities(self, data):
        sriov_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]

        try:
            if 'aggregate_instance_extra_specs:sriov_nic' in extra_specs:
                value1 = extra_specs['aggregate_instance_extra_specs:sriov_nic'].split(':')
                value2 = value1[0].split('-', 5)

                sriov_capability['hpa-capability-id'] = str(feature_uuid)
                sriov_capability['hpa-feature'] = 'sriovNICNetwork'
                sriov_capability['architecture'] = str(value2[2])
                sriov_capability['hpa-version'] = 'v1'

                sriov_capability['hpa-feature-attributes'] = []
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciCount',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value1[1])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciVendorId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[3])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciDeviceId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[4])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'physicalNetwork',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[5])})
        except Exception:
            self._logger.error(traceback.format_exc())

        return sriov_capability

    def _get_ovsdpdk_capabilities(self, data):
        ovsdpdk_capability = {}
        feature_uuid = uuid.uuid4()
        extra_specs = data["extra_specs"]
        viminfo = data["viminfo"]
        vimtype = data["vimtype"]
        libname = "dataProcessingAccelerationLibrary"
        libversion = "12.1"

        try:
            ovsdpdk_capability['hpa-capability-id'] = str(feature_uuid)
            ovsdpdk_capability['hpa-feature'] = 'ovsDpdk'
            ovsdpdk_capability['architecture'] = 'Intel64'
            ovsdpdk_capability['hpa-version'] = 'v1'

            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str in [None, '']:
                if vimtype in ["windriver", "starlingx"]:
                    libname = "dataProcessingAccelerationLibrary"
                    libversion = "17.2"
            else:
                if not isinstance(cloud_extra_info_str, dict):
                    try:
                        cloud_extra_info_str = json.loads(cloud_extra_info_str)
                    except Exception as ex:
                        logger.error("Can not convert cloud extra info %s %s" % (
                                     str(ex), cloud_extra_info_str))
                        return {}
                if cloud_extra_info_str :
                    cloud_dpdk_info = cloud_extra_info_str.get("ovsDpdk")
                    if cloud_dpdk_info :
                        libname = cloud_dpdk_info.get("libname")
                        libversion = cloud_dpdk_info.get("libversion")
            
            ovsdpdk_capability['hpa-feature-attributes'] = [
                {
                    'hpa-attribute-key': str(libname),
                    'hpa-attribute-value': '{{\"value\":\"{0}\"}}'.format(libversion)
                },]
        except Exception:
            self._logger.error(traceback.format_exc())

        return ovsdpdk_capability
