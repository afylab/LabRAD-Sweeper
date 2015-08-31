import labrad

class datasetDetails(object):
    def __init__(self,name,loc,independents,dependents):
        self.name         = name
        self.loc          = loc
        self.independents = independents
        self.dependents   = dependents
        self.vars         = independents + dependents

class dataLogger(object):
    def __init__(self,password):
        self.connection = labrad.connect(password=password)
        self.servers    = str(self.connection.servers).splitlines()
        
        if not ('data_vault' in self.servers):
            print("Data Vault is not running. Please run the Data Vault server, then restart the program.")
            self.can_log = False
        else:
            self.can_log = True
            self.dv      = self.connection.servers['data_vault']

        # The program will not new() a new file unless this variable is False. This is because files can
        # only be written to when opened with new(), and only one file can be opened at a time: if a new
        # file is made, the old one becomes unwritable. The program must finish, and close, the old file
        # before starting a new one.
        self.active = False

        # type of active dataset. 'read', 'write', or None
        self.active_type = None
        
        self.details = None

    def make_dataset(self,name,loc,indep,dep):
        '''Creates a new data set, and returns the number of the set created.'''
        if self.active:
            print("Error: there is already an active dataset. Please wait until it finishes.")
            return False

        self.dv.cd(loc)
        new = self.dv.new(name,indep,dep)
        self.details = datasetDetails(name,loc,indep,dep)
        self.active      = True
        self.active_type = 'write'
        return int(new[1].partition(' - ')[0])

    def dump_data(self,data):
        if not self.active:
            print("Error: tried to dump data with no active file.")
            return False

        if not (self.active_type == 'write'):
            print("Error: data set cannot be written to: it is in read-only mode.")

        if len(data[0]) != len(self.details.vars):
            print("Error: length of datum is %i, required length is %i."%(len(data[0]),len(self.details.vars)))
            return False

        try:
            self.dv.add(data)
            return True
        except:
            print("Error: invalid data. It should be a list of lists, and each sublist should have a number of entries equal to <independents> + <dependents>. Unitless (int, float, etc) entries also required.")
            return False

        return True

    def add_parameters(self,params):
        """Params should be a list of lists: [ [name, value], [name, value], ... ]"""
        if not self.active:
            print("Error: tried to add parameters with no active file.")
            return False
        
        if not (self.active_type == 'write'):
            print("Warning: parameters added to read-only file. This should only happen if the file was created in this session.")

        success = True
        for param in params:
            try:
                self.dv.add_parameter(param[0],param[1])
            except:
                print("Error: invalid or pre-existing parameter. Offending paramter is printed in next line.")
                print(param)
                print('\n')
                success = False
        return success

    def add_comments(self,comments):
        """Comments should be list of lists: [ [user, comment], [user, comment], ... ]"""
        if not self.active:
            print("Error: tried to add comments with no active file.")
            return False

        success = True
        for comment in comments:
            try:
                self.dv.add_comment(comment[1],comment[0])
            except:
                print("Error: invalid comment. Offending comment is printed in next line.")
                print(comment)
                print('\n')
                success = False
        return success

    def close_dataset(self):
        if not self.active:
            print("Error: cannot close data set, as no data set is open.")
            return False
        self.active      = False
        self.active_type = None
        self.details     = None



    # These are for adding comments/params to files that already exist.
    def add_comments_to_file(self,loc,num,comments):
        '''Adds comments to pre-existing file. comments should be of form [ [user, comment], [user, comment], ... ]'''
        if self.active:
            print("Error: cannot add comments to arbitrary file when a file is already open.")
            return False
        
        try:
            self.dv.cd(loc)
        except:
            print("Error: specified location does not exist.")
            return False

        files_raw = self.dv.dir()[1]
        files     = [int(fraw.partition(' - ')[0]) for fraw in files_raw]
        #print(files)
        if not (num in files):
            print("Error: specified file does not exist in the specified location.")
            return False

        try:
            self.dv.open(num)
            self.active      = True
            self.active_type = 'read'
            self.details     = 'no_details_needed'
        except:
            print("Error: unknown error opening existing file.")
            return False

        success = self.add_comments(comments)
        self.active      = False
        self.active_type = None
        self.details     = None
        return success
        

    def add_parameters_to_file(self,loc,num,parameters):
        if self.active:
            print("Error: cannot add parameters to arbitrary file when a file is already open.")
            return False

        try:
            self.dv.cd(loc)
        except:
            print("Error: specified location does not exist.")
            return False

        files_raw = self.dv.dir()[1]
        files     = [int(fraw.partition(' - ')[0]) for fraw in files_raw]
        #print(files)
        if not (num in files):
            print("Error: specified file does not exist in the specified location.")
            return False

        try:
            self.dv.open(num)
            self.active      = True
            self.active_type = 'read'
            self.details     = 'no_details_needed'
        except:
            print("Error: unknown error opening existing file.")
            return False

        success = self.add_parameters(parameters)
        self.active      = False
        self.active_type = None
        self.details     = None
        return success






testing = True
if __name__=='__main__' and testing:
    test=dataLogger('pass')


















