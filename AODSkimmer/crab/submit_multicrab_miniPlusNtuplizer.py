from CRABAPI.RawCommand import crabCommand
from CRABClient.ClientExceptions import ClientException
import CRABClient.UserUtilities
from XRootD import client
import XRootD.client.flags as flags
from optparse import OptionParser
from multiprocessing import Process
import os
import json
from datetime import datetime

xrdClient = client.FileSystem("root://cmseos.fnal.gov")

def parseArguments():
    parser = OptionParser()
    
    parser.add_option('-c', '--crabCmd',
                      dest = 'crabCmd',
                      default = '',
                      help = "crab command",
                      metavar = 'CMD')

    parser.add_option('-y', '--year',
                      dest = 'year',
                      default = '',
                      help = "Which year to process ('2018'(default)/'2017'/'2016')",
                      metavar = 'YEAR')

    parser.add_option("-f","--inFile",
                      dest = 'inFile',
                      default = '',
                      help = 'JSON file with input data or MC lists',
                      metavar = 'INFILE')

    parser.add_option("-t","--type",
                      dest="type",
                      default='',
                      help='Sample type, Data (1) or MC (0)',
                      metavar="TYPE")

    parser.add_option('-s','--signal',
                     dest="signal",
                     default='',
                     help='Is running signal (1) or not (0)',
                     metavar='SIGNAL')
    
    (options, arguments) = parser.parse_args()
    
    if arguments:
        parser.error("Found positional argument(s): %s." % (arguments))
    if not options.crabCmd:
        parser.error("(-c CMD, --crabCmd=CMD) option not provided.")
    if not options.year:
        parser.error("-y year option not provided")
    if not options.inFile:
        parser.error("-f input file option not provided")
    if not options.type:
        parser.error("-t type data (1) or mc (0) option not specified")
    if not options.signal:
        parser.error("-s : is running on signal (1) or not (0) option not specified")

    return options

def main():
    options = parseArguments()
    
    if 'CMSSW_BASE' not in os.environ.keys():
        print "Run cmsenv first!"
        return
    base_dir = os.environ['CMSSW_BASE']

    year = options.year
    samp_type = options.type

    config = CRABClient.UserUtilities.config()

    # Basic settings common to all runs 
    config.General.workArea = base_dir+'/src/iDMe/AODSkimmer/crab/submissions_miniNtuplizer/'
    config.General.transferOutputs = True
    config.General.transferLogs = True
    config.JobType.pluginName = 'Analysis'
    config.JobType.psetName = base_dir+'/src/iDMe/AODSkimmer/scripts/miniPlusElectronNtuplizer_cfg.py'
    config.JobType.allowUndistributedCMSSW = True
    config.JobType.numCores = 1
    config.Data.splitting = 'Automatic'
    #config.Data.totalUnits = 1
    #config.Data.splitting = 'FileBased'
    #config.Data.unitsPerJob = 1
    config.Data.publication = False
    config.Data.ignoreLocality = True
    config.Site.whitelist = ['T2_US_*', 'T2_DE_*', 'T2_EE_*', 'T2_ES_*', 'T2_GR_*', 'T2_HU_*', 'T2_IT_*', 'T2_RU_*', 'T2_UK_*']
    config.Site.storageSite = 'T3_US_FNALLPC'

    inFile = options.inFile
    samples = {}
    with open(inFile) as f:
        samples = json.load(f)
    for samp in samples.keys():
        for subsample, dataset in samples[samp].items():
            output_base = '/store/group/lpcmetx/iDMe/Samples/Ntuples/background/{0}/{1}/{2}/'.format(year,samp,subsample)
            xrdClient.mkdir(output_base,flags.MkDirFlags.MAKEPATH)
            config.Data.outLFNDirBase = output_base
            config.Data.inputDataset = dataset
            config.General.requestName = 'iDMe_' + subsample + datetime.now().strftime("_%Y_%m_%d-%H_%M")
            config.JobType.outputFiles = ['{0}.root'.format(subsample)]
            config.JobType.pyCfgParams = ['numThreads=1',
                                          'outfile={0}.root'.format(subsample),
                                          'data={0}'.format(samp_type),
                                          'signal={0}'.format(options.signal)]
            print 'Submitting for input dataset {0}'.format(subsample)
            #crabCommand(options.crabCmd, config = config)
            kwargs = {'config':config}
            p = Process(target=crabCommand,args=(options.crabCmd,),kwargs=kwargs)
            p.start()
            p.join()

if __name__ == '__main__':
    main()
