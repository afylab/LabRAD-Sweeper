"""
LabRAD Sweeper 0.2.0
Data Vault Interface

"""
import labrad
from labrad.units import Value

class DataSet(object):
	def __init__(self,name,location,independents,dependents):
		self.name         = name         # name of the data set
		self.location     = location     # location of the data set in data vault
		self.independents = independents # list of dependent variables
		self.dependents   = dependents   # list of independent variables
		self.variables    = independents+dependents # list of all variables
		self.vartotal     = len(self.variables) # total length of data entries

		self.connection = labrad.connect()
		self.dv         = self.connection.data_vault
		self.ctx        = self.connection.context()
		# self.dv           = CONNECTION_HANDLER.dv            # connection to data vault
		# self.ctx          = CONNECTION_HANDLER.get_context() # context to use for data vault
		self.ctx_expired  = False                            # whether or not this context has been expired for this data set
		self.dataset_open = False                            # whether or not the dataset is open in this context

		self.comments   = [] # list of comments     that have been added but not yet written to the data set. Stored [ [comment, user], [comment, user], ... ]
		self.parameters = [] # list of parameters   that have been added but not yet written to the data set. Stored [ [name, value],   [name, value],   ... ]
		self.data       = [] # list of data entries that have been added but not yet written to the data set. Stored [ [independents+dependents],        ... ]
		self.tags       = [] # list of tags. Since tags can be overwritten, this list corresponds to the data set's tags.

	def create_dataset(self):
		if self.dataset_open:raise ValueError("Error: tried to create a dataset that already exists (and is open)")
		if self.ctx_expired:raise ValueError("Tried to use data vault with expired context")

		self.dv.cd(self.location,True,context=self.ctx)                          # move to the directory & create it if it doesn't exist
		self.dv.new(self.name,self.independents,self.dependents,context=self.ctx) # create the data set. Only info it needs immediately is the name & variables
		self.dataset_open = True

	def close_dataset(self):
		self.dataset_open = False
		self.ctx_expired  = True
		self.connection.disconnect()
		print("LabRAD connection closed for DataSet object with name ({name})".format(name=self.name))

	def add_comments(self,comments,write=False):
		if not comments:comments = []
		for comment in comments:
			if type(comment) not in [list,tuple]:                      raise ValueError("Error: invalid comment type. Should be list or tuple, got {ctype}".format(ctype=type(comment)))
			if len(comment) != 2:                                      raise ValueError("Error: invalid comment. Should be [comment, user]; got {comment}".format(comment=comment))
			if (type(comment[0]) != str) or (type(comment[1]) != str): raise ValueError("Error: comment types should be [string, string]; got [{t1}, {t2}]".format(t1=type(comment[0]),t2=type(comment[1])))
		self.comments += comments
		if write:self.write_comments()

	def write_comments(self):
		if not len(self.comments):return
		if not self.dataset_open:raise ValueError("Cannot write comments to a dataset that hasn't been opened.")
		if self.ctx_expired:raise ValueError("Tried to use data vault with expired context")
		done = False
		while not done:
			if len(self.comments) == 0:
				done=True
				continue
			comment = self.comments.pop()
			self.dv.add_comment(comment[0],comment[1],context=self.ctx)

	def add_parameters(self,parameters,write=False):
		if not parameters:parameters=[]
		for param in parameters:
			if type(param) not in [list,tuple]: raise ValueError("Error: invalid parameter type. Should be list or tuple, got {ptype}".format(ptype=type(param)))
			if len(param) != 3:                 raise ValueError("Error: invalid parameter. should be [name,units,value]; got {param}".format(param=param))
			if type(param[0]) != str:           raise ValueError("Error: invalid type for parameter name. Should be string, got {ntype}".format(ntype=type(param[0])))
		self.parameters += parameters
		if write:self.write_parameters()

	def write_parameters(self):
		if not len(self.parameters):return
		if not self.dataset_open:raise ValueError("Cannot write parameters to a dataset that hasn't been opened.")
		if self.ctx_expired:raise ValueError("Tried to use data vault with expired context")
		done = False
		while not done:
			if len(self.parameters) == 0:
				done=True
				continue
			param=self.parameters.pop()
			self.dv.add_parameter(param[0],Value(param[2],param[1]),context=self.ctx)

	def add_data(self,data,write=False):
		if not data:data=[]
		for datum in data:
			if type(datum) not in [list,tuple]: raise ValueError("Error: invalid type for data. Should be list or tuple of [independents,dependents]; got type {dtype}".format(dtype=type(datum)))
			if len(datum) != self.vartotal:     raise ValueError("Error: got data of invalid length. Was {datalen}, should be {vartotal}".format(datalen=len(datum),vartotal=self.vartotal))
		self.data+=data
		if write:self.write_data()

	def write_data(self):
		if not len(self.data):return
		if not self.dataset_open:raise ValueError("Cannot write data to a dataset that hasn't been opened.")
		if self.ctx_expired:raise ValueError("Tried to use data vault with expired context")
		self.dv.add(self.data,context=self.ctx)
		self.data=[]
