#!/usr/bin/env python3
from data.recon import Recon
from data.recon import ReconFiles
from data.session import Session
import re
from src.masterLogger import masterLogger
logger = masterLogger('logs', 'logs/lib.log', __name__)

class Reconnaissance():
    '''
    Main use is to gain info on the session, store it, and use it later.
    @TODO
    make different methods for powershell and cmdshell
    timeout function for powershell if it's blocked
    '''

    def gatherNetwork(self, msfclient, sessionInput):
        try:
            session = Session.objects(_id=sessionInput).first()
            ip = msfclient.client.sessions.session(sessionInput).run_psh_cmd("ipconfig /all")
            if session:
                recon = Recon.objects(session_id=sessionInput).first()
                if recon:
                    self.parseIPData(recon, ip)
                else:
                    recon = Recon()
                    recon.session_id = sessionInput
                    recon._id = sessionInput
                    session.recon_id.append(recon.session_id)
                    self.parseIPData(recon, ip)
            recon.save()
            session.save()
        except Exception as msg:
            logger.info(msg)
            print("There was an error!")
            pass

    def gatherCurrentAdmin(self, msfclient, sessionInput):
        try:
            admin = msfclient.client.sessions.session(sessionInput).run_psh_cmd("net sessions")
            session = Session.objects(_id=sessionInput).first()
            if session:
                recon = Recon.objects(session_id=sessionInput).first()
                if recon:
                    for lines in admin.splitlines():
                        if not 'Access is denied.' in lines:
                            recon.isAdmin = True
                        else:
                            recon.isAdmin = False
                else:
                    recon = Recon()
                    recon.session_id = sessionInput
                    recon._id = sessionInput
                    session.recon_id.append(recon.session_id)
                    for lines in admin.splitlines():
                        if not 'Access is denied.' in lines:
                            recon.isAdmin = True
                        else:
                            recon.isAdmin = False
            recon.save()
            session.save()
        except Exception as msg:
            logger.info(msg)
            print("There was an error!")
            pass

    def gatherWhoAmI(self, msfclient, sessionInput):
        try:
            whoami_input = []
            whoami = msfclient.client.sessions.session(sessionInput).run_psh_cmd("whoami")
            session = Session.objects(_id=sessionInput).first()
            if session:
                recon = Recon.objects(session_id=sessionInput).first()
                if recon:
                    whoami_input = whoami.splitlines()
                    recon.whoami = whoami_input[1]
                else:
                    recon = Recon()
                    recon.session_id = sessionInput
                    recon._id = sessionInput
                    session.recon_id.append(recon.session_id)
                    for lines in whoami.splitlines():
                        recon.whoami = lines
            recon.save()
            session.save()
        except Exception as msg:
            logger.info(msg)
            print("There was an error!")
            pass
    
    def gatherPWD(self, msfclient, sessionInput):
        try:
            current_pwd = msfclient.client.sessions.session(sessionInput).run_with_output('pwd')
            session = Session.objects(_id=sessionInput).first()
            if session:
                recon = Recon.objects(session_id=sessionInput).first()
                if recon:
                    if recon.pwd == current_pwd:
                        pass
                    else:
                        recon.pwd = current_pwd
                        reconfiles = ReconFiles()
                        reconfiles.dir_name = current_pwd
                        recon.directory.append(reconfiles)
                else:
                    recon = Recon()
                    recon.session_id = sessionInput
                    recon._id = sessionInput
                    session.recon_id.append(recon.session_id)
                    recon.pwd = current_pwd
                    reconfiles = ReconFiles()
                    reconfiles.dir_name = current_pwd
                    recon.directory.append(reconfiles)
            recon.save()
            session.save()
        except Exception as msg:
            logger.info(msg)
            print("There was an error!")
            pass
    
    def gatherFiles(self, msfclient, sessionInput):
        try:
            desc_files = ['Mode', 'Size', 'Type', 'Last', 'Modified', 'TimeZone', 'Name']
            listofFiles = msfclient.client.sessions.session(sessionInput).run_with_output('ls').splitlines()
            session = Session.objects(_id=sessionInput).first()
            if session:
                recon = Recon.objects(_id=sessionInput).first()
                directory = Recon.objects().filter(directory__dir_name=recon.pwd)
                if directory:
                    for r in directory:
                        for d in r.directory:
                            if d.gathered == False:
                                d.gathered = True
                                for f in listofFiles:
                                    file = self.parseFileData(f)
                                    if not file:
                                        pass
                                    else:
                                        files_mapped = dict(zip(desc_files, file))
                                        d.files.append(files_mapped)
                                r.save()
                            else:
                                current_files = []
                                for _dict in d.files:
                                    current_files.append(_dict['Name'])
                                for f in listofFiles:
                                    file = self.parseFileData(f)
                                    if file[6] in current_files:
                                        pass
                                    else:
                                        files_mapped = dict(zip(desc_files, file))
                                        d.files.append(files_mapped)
                                r.save()
        except Exception as msg:
            logger.info(msg)
            print("There was an error!")
            pass

    def parseFileData(self, f):
            file = f.split()
            if not f:
                pass
            elif 'Listing' in f:
                pass
            elif '=====================================' in file[0]:
                pass
            elif '----' in f:
                pass
            elif 'Mode' in file[0]:
                pass
            else:
                return file
    
    def parseIPData(self, recon, ip):
        for lines in ip.splitlines():
            if 'IPv4' in lines:
                found_ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}',lines)
                recon.ip_address = found_ip[0]
            if 'Default Gateway' in lines:
                found_gateway = re.findall( r'[0-9]+(?:\.[0-9]+){3}',lines)
                recon.defaultgateway = found_gateway[0]
            if 'DNS Servers' in lines:
                found_dns =  re.findall( r'[0-9]+(?:\.[0-9]+){3}',lines)
                recon.dns = found_dns[0]
            if 'DHCP Server' in lines:
                found_dhcp = re.findall( r'[0-9]+(?:\.[0-9]+){3}',lines)
            if 'Subnet Mask' in lines:
                found_subnet_mask = re.findall( r'[0-9]+(?:\.[0-9]+){3}',lines)