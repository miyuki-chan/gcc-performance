DEFS        = ['_GNU_SOURCE', 'SPEC_CPU', 'SPEC_CPU_LP64', 'NDEBUG']

OTHER_DEFS  = { \
        '400.perlbench':    ['SPEC_CPU_LINUX_X64', 'PERL_CORE'],
        '433.milc':         ['FN', 'FAST' 'CONGRAD_TMP_VECTORS', 'DSLASH_TMP_LINKS'],
        '445.gobmk':        ['HAVE_CONFIG_H'],
        '447.dealII':       ['BOOST_DISABLE_THREADS'],
        '462.libquantum':   ['SPEC_CPU_LINUX'],
        '473.astar':        ['SPEC_CPU_LITTLE_ENDIAN'],
        '482.spihx3':       ['HAVE_CONFIG_H'],
        '483.xalancbmk':    ['SPEC_CPU_LINUX', 'APP_NO_THREADS', 'XALAN_INMEM_MSG_LOADER',
                             'PROJ_XMLPARSER', 'PROJ_XMLUTIL', 'PROJ_PARSERS',
                             'PROJ_SAX4C', 'PROJ_SAX2', 'PROJ_DOM', 'PROJ_VALIDATORS',
                             'XML_USE_NATIVE_TRANSCODER', 'XML_USE_INMEM_MESSAGELOADER']
}

INCLUDES    = { \
        '403.gcc':          ['.'],
        '433.milc':         ['.'],
        '445.gobmk':        ['.', '..', './include', '../include'],
        '482.sphinx3':      ['.', 'libutil'],
        '471.omnetpp':      ['.', 'omnet_include', 'libs/envir'],
        '483.xalancbmk':    ['.', 'xercesc', 'xercesc/dom', 'xercesc/dom/impl',
                             'xercesc/sax', 'xercesc/util/MsgLoaders/InMemory',
                             'xercesc/util/Transcoders/Iconv', 'xalanc/include']
}

CRUTCHES    = { \
        '400.perlbench':    ['-fgnu89-inline'],
        '450.soplex':       ['-std=c++98'],
}

