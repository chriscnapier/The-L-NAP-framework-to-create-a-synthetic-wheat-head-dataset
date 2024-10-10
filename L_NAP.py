
"""
The L_NAP application with Parametric expressions. April 2023
"""
import types		# types.FunctionType to recognise function names
import traceback	# Caller address
import inspect		# To find correct number of fn arguments
import numpy as np	# Stochastic random normal parameter adjustment
import random		# Stochastic rule selection

class L_NAP:		# class name is the same as this import file name

	def __init__(self, run_arg):
		#
		# Set the L-system parameters dict p, either directly from run_arg,
		# or Import from the given run_arg (+".py") and use locals() to: 
		# 
		# parameters_p of run_arg, and
		# store into dict p_routines, names: addresses of
		# _p functions of the run, found by locals(), for
		# use in Rule() fn to set parameters.
		#
		# IMPORTANT: 
		#   self.p is same address as p within the run_arg, so that 
		#   a change in self.p['stage'], for example, changes p['stage'] 
		#	unless p is not presnet in run_arg, in which case we have 
		#	only a local self.p .
		# 
		self.p_routines = {}	#dict of_p routines as {'name':address,}
		self.run_arg = "LN"
		self.dir = dir(L_NAP)
				
		if isinstance(run_arg, dict):
			self.p = run_arg
			self.p['PlantNr'] = 0
			self.p['stage0'] = 0
			self.p['stage1'] = self.p['stage']
			
		elif isinstance(run_arg, str):
			#
			# Remove an extension
			#
			ext = run_arg.find(".")
			if ext > 0:
				run_arg = run_arg[0:ext] 

			# import "run_arg", a _p file, and get parameter fn names
			self.run_arg = run_arg
			exec(f"from {run_arg} import *")
			loc = locals()
		
			keys = list(loc)
			for key in keys:
				if key.endswith("_p"):
					self.p_routines[key] = loc[key]
		
			fn = self.p_routines['Parameters_p'] \
					if 'Parameters_p' in self.p_routines else None
			self.p = fn() if fn else {}			
		#
		# Selected parameter values for current run
		#
		self.p['stage'] = 0
		if 'stage0' not in self.p:
			self.p['stage0'] = 0
		if 'stage1' not in self.p:
			self.p['stage1'] = 3
			
		self.log = self.p['log'] if 'log' in self.p else True
		
		# File operations relating to current run and final stage number
		# Name cmds file after rules file, not parameters file.
		if self.run_arg.endswith("_p"):
			name = self.run_arg[0:-2]
		else:
			name = self.run_arg
		self.cmds_filename = f"{name}.cmds"	
		self.cmds_file = open(self.cmds_filename,"w")
		# Allow application to write to cmds_file
		self.p['cmds_file'] = self.cmds_file
		
		# List buffers for computed rules, results
		self.rules = []
		self.rewrites = []
		self.result = []
		
		# Either repeat all rendoms in run or start randomly
		# and save Random obect as p['Random']
		self.seed = self.p["seed"] if 'seed' in self.p else None
		self.p['Random'] = np.random.RandomState(self.seed) 
			
	#
	# Definition of a Production rule, (a main-rule) and a definition of
	# what it produces, namely *rules.	
	#
	# Append *rules to result.	Pl_num
	# Caller must clear result after (final) use.
	#	
	def __call__(self, *rules):
		#
		# Get the name of the caller, such as "Axiom", using traceback,
		# and hence the _p function, such as "Axiom_p",
		# and call that _p fuction to get p as a dictionary of key:value 
		# pairs, which are to be applied to all produced *rules defined 
		# in this current Rule.
		# The actual call args have been stored by the caller ,,,
		#
		p = None	# No dictionary
		stack_trace = traceback.extract_stack(limit=5)
		caller_detail = f'{stack_trace[-2]}'
		caller = caller_detail.split()[-1]
		l = len(caller)
		if l > 1:
			caller = caller[0:l-1]
			name = caller + '_p'		# a name such as: "Axiom_p"
			fn = self.p_routines[name] if name in self.p_routines else None
			if fn:
				p = fn()	# We are in Rule, and we want to know the
							# calling main_rule, such as Axiom to get
							# its parameter dict into p.
			#				
			# Note: in command() the call_args of each main_rule are 
			# stored into self.p, which is same address
			# as external Parameters_p

		#if not p or not isinstance(p, dict):
		#	print(f"**** Warn: {self.run_arg}.py: Function {name}(), has no parameters\n") 
		#
		# Recursively append rules to result list,
		# with correct single parameters dict attached
		#
		self.append_rules_to_result(p, rules)

		return None # To avoid return stmt in every L_NAP Rule def
					# self.perform() picks up self.result list instead.	
		
	def translate_string_to_result(self, p, rule):
		for ch in rule:
			if ch in translate:
				chat = translate[ch] 
			elif ch in self.locals:
				chat = self.locals[ch]
				
			# if the rule needs one argument and we have p, use it
			argspec = inspect.getargspec(chat)
			if p and len(argspec[0]) == 1:
				chat = (chat,p)
			else:
				chat = (chat,)
			self.result.append(chat)
		
	def locals(self, loc):
		self.locals = loc
		x=1

	def rule_base_terminal(self, rule):

		tup_rule = isinstance(rule, tuple)
		if tup_rule:
			rul = rule[0]
			args = rule[1:]
		else:
			rul = rule
			args = None
		
		routine_name = self.rule_name(rul)
		if hasattr(L_NAP, routine_name): 
			rul = eval("self."+routine_name)
			return (rul, True)	#No args on Draw, etc
		else:
			return (rule, False)
			
	def is_main_rule(self, rule):
		if len(self.p_routines) > 0:
			rule_name_p = self.rule_name(rule) + "_p"
			for routine in self.p_routines:
				if rule_name_p == routine:
					return True
			return False
		else:
			fn = rule
			if isinstance(fn, types.FunctionType):
				fn = f'{fn}'.split()[1]
				return True
			elif isinstance(fn, types.MethodType):
				fn = f'{fn}'.split()[2]
				i = fn.find('.')
				if i > 0:
					fn = fn[i+1:]
				return False
			return False
		
	def type_of_rule(self, rule):
		#
		# Determine the type of rule, and return:
		#    (rule_type, routine, args)
		#
		# 0: str   representing standard L-system
		# 1: list  representing nested rules
		# 2: tuple index 
		# 3: main-rule as tuple_call
		# 4: main-rule without arguments
		# 5: Draw(p), etc which are terminal rules (no further expansil,on)
		# 6: Dict probability
		#
		if isinstance(rule, str):
			return (0,rule,None)
			
		elif isinstance(rule, list):
			return (1,rule,None)
			
		elif isinstance(rule, types.FunctionType):
			
			routine, is_terminal = self.rule_base_terminal(rule)
			if is_terminal:
				return (5,routine,None)
			else:
				return (4,routine,None)
				
		elif isinstance(rule, tuple):
			
			if isinstance(rule[0], int):
				routine = rule[1]
				index = rule[0]
				return (2, routine, index)
				
			elif isinstance(rule[0], types.FunctionType):
				routine, is_terminal = self.rule_base_terminal(rule)
				if is_terminal:
					return (5,routine,None)
				else:
					return (3,routine,None)
					
		elif isinstance(rule, dict):
			return (6, rule, None)
		
		return (-1,None,None)
		 
	def append_rules_to_result(self, p, rules):
		#
		# The type of rule:
		# 0: str   representing standard L-system
		# 1: list  representing nested rules
		# 2: tuple index 
		# 3: main-rule as tuple_call
		# 4: main-rule without arguments
		# 5: Draw(p), etc which are terminal rules (no further expansil,on)
		# 6: Dict probability
		#
		
		for rule in rules:
			rule_type,routine,index = self.type_of_rule(rule) 
			if rule_type == -1:
				break
				
			# If str-type rules such as "F[+X]"  are used, then the
			# above fn locals must be called before Next_stage, with
			# loc=locals() of caller.
			elif rule_type == 0:
				self.translate_string_to_result(p, routine)
				
			elif rule_type == 1:				
				self.result.append((Save,0))
				self.append_rules_to_result(p, routine)
				self.result.append((Restore,0))
			#
			# a tuple rule SETS new key:value of 'index':rule[1] into p,
			# to tell Draw, etc to select_indexed using that key rule[1]
			#	
			elif rule_type == 2:
				#print(f"Tuple dict index rule: {rule}\n")	
				if p:
					p_copy = p.copy()
					p_copy['index'] = index
					rule = (routine, p_copy)
							
					self.result.append(rule)
			#
			# a tuple rule SETS new key:value of 'index':rule[1] into p,
			# to tell Draw, etc to select_indexed using that key rule[1]
			#	
			elif rule_type == 5:
				#print(f"Tuple rule (Draw,p etc.) : {rule}\n")
				if p:
					rule = (routine, p)
				else:
					rule = (routine,)	
							
				self.result.append(rule)
				
			elif rule_type == 3:  
				# if the rule needs one argument and we have p, use it
				#argspec = inspect.getargspec(routine)
				#if p and len(argspec[0]) == 1:
				#	rule = (routine,p)								#2
				#else:
				#	rule = (routine,)
				self.result.append(routine)
				
			elif rule_type == 4:
				self.result.append(routine)
			#
			# A dict of {index:routine,} pairs, indicating that within 
			# a dict one of the routines is selected for execution with 
			# probability(index-1), where probability(index-1) is an
			# L-system parameter. (index is 1-based)
			#
			# either {1: A, 2: B, 3: C}
			# or     {1: D}
			#				
			elif rule_type == 6:
				if p and 'prob' in p: 
					new_rule = {}	
					for index in rule:				# 1,2,3,...
						routine = rule[index] 		# Given routine fn
						prob = p['prob']			# Probability of
						if isinstance(prob, tuple):	# activating routine
							prob = prob[index-1]	# at index or
													# single value		
						prob = 10*index + prob		# Unique key 
						new_rule[prob] = (routine,p) # add to new_rule
													 # with paramaters
					self.result.append(new_rule)	# add new_rule to result			
	#
	# The Grow rules for this stage are defined in self.rules
	# Perform the rules into rewrites, from which cmds are written
	# to file, with file(s) closed after last stage.
	def grow(self):
		for rule in self.rules:
			
			# dict_rule requires selection using index
			if isinstance(rule, dict):
				rs_rule = self.rule_select(rule)
				if rs_rule:
					self.perform(rs_rule)
			# non-dict" directly perform rule
			else:
				self.perform(rule)	
				
		# log rewrite to cmds_file (recursively)
		for rewrite in self.rewrites:
			self.cmds_log(rewrite)
		
		# After the last stage, when we are NOT writing a number of 
		if self.p['stage'] > self.p['stage1']:
			if self.p['PlantNr'] == 0:
				self.close_files()	
				
	# Log a single rewrite to the cmds_file
	# (internal recursive calls when rewrite is a list of rewrites)			
	def cmds_log(self, rewrite):		
		# Print requested range stage_0..stage_1 (inclusive)
		if self.p['stage'] >= self.p['stage0'] and \
			self.p['stage'] <= self.p['stage1']: 		
			# A final draw command is a string
			if isinstance(rewrite, str):
				self.cmds_file.write(rewrite + "\n")
			#
			# Otherwise it may be a tuple, a fn rule yet to be rewritten
			# which if its arg is a dict is recreated that  float 
			# values have only 4 digits.  
			#		
			elif isinstance(rewrite, tuple):
				fn = rewrite[0]
				if isinstance(fn, types.FunctionType):
					fn = f'{fn}'.split()[1]
					
				# Extract method name such as "Draw" from "L_NAP.Draw"	
				elif isinstance(fn, types.MethodType):
					fn = f'{fn}'.split()[2]
					i = fn.find('.')
					if i > 0:
						fn = fn[i+1:]
					
				lisrew = list(rewrite)
				lisrew[0]=fn
				xxx=1
				
				#--arg = ''
				if len(rewrite) >= 1:	#CCN 3July2023 ">=1" not '>1'
					self.cmds_file.write(f"#->\t({fn},{rewrite[1:]})\n")
				else:
					self.cmds_file.write(f"{fn}")	#???
			elif isinstance(rewrite, types.FunctionType):
				fn = rewrite
				if isinstance(fn, types.FunctionType):
					fn = f'{fn}'.split()[1]
				arg = ''
				self.cmds_file.write(f"#{fn}\n")#BAD LAD incorrect log of single name
				
			elif isinstance(rewrite, list):
				self.cmds_file.write(f"#\tSave()\n")
				for rew in rewrite:
					self.cmds_log(rew)
				self.cmds_file.write(f"#\tRestore()\n")			

	def dict_truncate_float(self, arg):
		arg2 = '{'
		for key in arg:
			value = arg[key]
			if isinstance(value, float):
				value = f'{value:.4f}'
			arg2 += f"'{key}':{value},"
		arg2 += '}'
		return arg2
	#
	# Perform L-system standard rule, 
	# by appending it to rewrites.
	# Special case: Recurse on an L-system branch indicated by an 
	# input list, which is stored in rewrites with brackets '[' and ']'
	#		
	def perform(self, rule):
		cmd = ""
		if isinstance(rule, str): 
			#------rules = self.translate(str)
			self.rewrites.append(rule)
			
		# Append the current pose and this whole rule to the future
		elif isinstance(rule, list): 			
			pose = ""
			self.perform(Save)
			for ru in rule:
				self.perform(ru)
			self.perform(Restore)			
		# Perform the single user rule with its arguments
		elif isinstance(rule, tuple): 
			cmd = self.command(rule)
			if cmd is None:
				for re in self.result:
					self.rewrites.append(re)
					#--self.cmds_file.write(f"#---Perform is appending result1: {re}\n")				
				self.result = []			
			# rule Draw returns a tuple of commands in cmd - we must
			# separate them into rewrites
			elif isinstance(cmd, tuple):
				for cm in cmd:
					self.rewrites.append(cm)
			else:
				self.rewrites.append(cmd)		
		elif isinstance(rule, types.FunctionType):
			rule = (rule,)
			cmd = self.command(rule)
			if cmd is None:
				for re in self.result:
					if re is not None:
						self.rewrites.append(re)
						##self.cmds_file.write(f"#---Perform is appending result2: {re}\n")
				self.result = []	#CCN Fix by adding this line
			else:
				self.rewrites.append(cmd)
				
	# Calculate the next derivation stage
	def next_stage(self, axiom):
		if self.p['stage'] == 0:

			# Get initial plant rules, by calling given local axiom fn
			axiom()

			self.rules = self.result.copy()
			self.result = []	
			
			for rule in self.rules:
				self.cmds_log(rule)
				
		if self.p['stage'] < self.p['stage1']:
			if self.p['stage'] >= self.p['stage0']: 
				self.cmds_file.write(f"\n# stage: {self.p['stage']+1}\n")
				
			if self.p['stage'] > 0:	
				self.rules = []
				for rule in self.rewrites:
					if rule is not None:
						self.rules.append(rule)						
				self.rewrites = []
				
			self.p['stage'] += 1
			return True
		else:
			self.rules = []
			self.rewrites = []
			self.result = []
			
			self.cmds_file.write(f"\tfinish({self.p['PlantNr']})\n")
			
			return False
			
		
	# Get the m factors at n values per factor, from the given number 
	def get_factors(self, number, mp, nv):
		factors = []
		for i in range(mp):	# each parameter
			x = number//nv	# nv is number of values
			y = nv * x
			factors.append(number-y)
			number = x
		return factors

	# Set a named L-system parameter to value	 'deltas':[m][n]	
	def set_lsystem_parameter(self, m,n):
		#paras = p['deltas'][m]
		name  = self.p['deltas'][m][0]
		value = self.p['deltas'][m][n+1]
		self.p[name] = value
		if name == 'Grain_count':
			self.p['stage0'] = value
			self.p['stage1'] = value
		return (name, value)			
			
	# Start a new object or close output file and finish
	def next_plant(self):
		# If no more plants required close output file(s) and say False
		if self.p['Plants'] == 0:
			self.close_files()
			return False

		# Next plant
		self.p['PlantNr'] += 1

#
#  'deltas': (('Grain_count', 50, 70, 90, 110), ('7',   30,  40,  50,  60), 
#			  ('5',  2,  5,  8,  11), ('3', 0.30,0.45,0.60,0.75,
#
		plantnr = self.p['PlantNr'] # set in L_NAPA_p.py
		mp = 1
		nv = len(self.p['deltas'][0]) - 1
		factors = self.get_factors(plantnr-1, mp, nv)
		
		xx=1
		for m, n in enumerate(factors):
			#reverse_m = m #--m_-m-1
			setting = self.set_lsystem_parameter(m,n)
			#self.cmds_file.write(f"{}"
			
		
		# Create model m with its np parameter values set
		# Reduce plant requied-count, and output next plant number 
		# at new stage 0

		self.p["Plants"] -= 1

		self.cmds_file.write(
			f"\n#----------------------------------------"
			f"----------------------------\n"
			f"\tplantnr({self.p['PlantNr']})	# Start\n")
		
		# Log the variable parameters for this plant	
		for m, delta in enumerate(self.p['deltas']):
			key = delta[0]
			value = self.p[key]
			self.cmds_file.write(
			f"\n# Plant: {plantnr}: has parameter {key}: {value}")
		self.cmds_file.write("\n")

		# Reset to stage 0 for next plant
		self.p['stage'] = 0

		self.cmds_file.write(
			f"\n# stage: {self.p['stage']}, stage0:{self.p['stage0']}, stage1: {self.p['stage1']}\n")
		return True
				
	#
	# Return the printable rule_name
	#
	def rule_name(self, rule):
		if isinstance(rule, dict):
			keys = list(rule.keys())
			rule = rule[keys[0]]
			
		if isinstance(rule, str):
			return rule

		elif isinstance(rule, list):
			name = '['
			for ru in rule:
				name += self.rule_name(ru)
				name += ','
			name += ']'
			return name	
					
		elif isinstance(rule, tuple):
			fn = f"{rule[0]}".split()[1]
			if len(rule) == 1:
				return f"{fn}"
			else:
				args = ""
				for n in range(len(rule)):
					if n > 0:
						args += f"{rule[n]}"
						if n < len(rule)-1:
							args += ","
				return f"{fn}({args})"
				
		elif isinstance(rule, types.FunctionType):
			fn = f"{rule}".split()[1]		
			return f"{fn}"	
					
		else:
			return '['+f"{rule}"+']'						
	#
	# Perform a Rule by calling the given fn at rule[0], with the 
	# given arguments at rule[1:], and save the call_args
	#
	def command(self, rule):
		lrule = len(rule)
		cmd = None # ""
		#
		# Execute a main_rule (xxx is a main_rule if routine
		# xxx_p is found in the run parameters file
		#
		if self.is_main_rule(rule[0]):
			#
			# Store in dict this main_rule_name and its call arguments
			# to represent the latest call to each main_rule
			# Note: call_args can be empty, as (), and *() is valid
			#
			main_rule = rule[0]
			main_rule_name = self.rule_name(main_rule)
			call_args = rule[1:]
			#
			# We add the main_rule arguments, into 
			# self.p['rule_name_args'], which is at same address as 
			# global p.
			#
			key = main_rule_name + '_args'
			self.p[key] = call_args

			cmd = rule[0](*call_args)
		
		# Draw, etc terminal rule as:    (rul, (p,index))
		elif lrule == 2:
			call_args = rule[1:]
			cmd = rule[0](*call_args)	# rul(p, index)
	
		return cmd

	"""
	Return one of the dict rule's or None by a selection based on key:
	EITHER: Conditional expression string such as  'y <= 3'
	OR:     Random fractional keys in dict_rules, such as Prob(0.33),
			(in other words a float or int key),
	"""
	def rule_select(self, dict_rule):
		ru = None
		keys = list(dict_rule.keys())
		# Conditional expressions, such as 'y <= 3', which is a string
		if isinstance(keys[0], str):
			for i,key in enumerate(keys):
				if isinstance(key, str):
					if len(key) == 0 or eval(key):
						ru = dict_rule[key]
						break	
		# Probability expression, which is float
		elif isinstance(keys[0], (float, int)):	
			rand0to1 = random.random()
			
			# define that No rule applied and no previous fractional value
			fracts = 0.
			#find which rule by fractional sum
			for i,key in enumerate(keys):
				if isinstance(key, (float, int)):
					fract = key - math.trunc(key)
					fracts += fract
					if rand0to1 < fracts:
						ru = dict_rule[key]
						self.cmds_file.write(
		f"Rand0to1: {rand0to1:.4f} leads to key: {key} rule: {ru}\n")
						break
		return  ru	
		
	def close_files(self):
		#-self.rules_file.close()
		self.cmds_file.write("\n")
		self.cmds_file.close()
#-----------------------------------------------------------------------	
# Pre-defined L_NAP rules
#
	#
	# Perform an indexed select of 'key' value(s) from dict p, using the
	# constant key of 'index' item already in p, OR return the default 
	# single key value or the keyed value at index 0.
	#
	def select_indexed(self, p, key, default=0):
		value = p[key] if key in p else default
		"""
		if isinstance(value, tuple):
			i = p['index'] if 'index' in p else 0
			if i >= 0 and i < len(value):
				return value[i]		# an indexed value
			else:
				return value[0]		# the value at index 0
		else:
		"""
		return value			# the p[key] or default value
			
	def Curve(self, p):
		"""
		Draw a curved line, as a stalk or Awn, using given pitch, turn 
		and draw length and width values, to cmd lines, for later 
		output to cmds file.
		""" 
		cmd = ''
		rule = p['rule'] if 'rule' in p else ''			
		if 'curve' in p:
			for pitch, turn, length, width in p['curve']:
				if pitch != 0:
					arg = f'pitch_up(angle={pitch:0.4f})'
					cmd += f"\n\t{arg:<54}#'.' : {rule} Pitch"
					
				if turn != 0:
					arg = f'turn_left(angle={turn:0.4f})'
					cmd += f"\n\t{arg:<54}#'.' : {rule} Turn"

				if length > 0 and width > 0:
					arg = f'draw(length={length:0.4f}, width={width:0.4f})'
					cmd += f"\n\t{arg:<54}#'F' : {rule} Draw"
					
		#if len(cmd) <= 0 ?? invalid syntex??
		#	cmd = None
		return cmd
			
	def Draw(self, p):	
		"""
		Draw: Cylinder of given 'draw' size with 'rule' name annotation
		"""
		cmd = None
		length, width = p['draw'] if 'draw' in p else (0,0)
		if length > 0 and width > 0:
			rule = p['rule'] if 'rule' in p else ''			
			arg = f'draw(length={length:0.4f}, width={width:0.4f})'
			cmd = f"\t{arg:<54}#'F' : {rule} Draw"
		return cmd

	def Internode(self, p):	
		return self.Draw(p)
	def Inter(self, p):	
		return self.Draw(p)
	def F(self, p):	
		return self.Draw(p)
	def Move(self, p):
		cmd = None
		length = self.select_indexed(p, 'move')
		if length > 0:			
			rule = p['rule'] if 'rule' in p else ''	
			arg = f'move(length={length:0.4f})'
			cmd = f"\t{arg:<54}#'f' : {rule} Move"
		return cmd
	def f(self, p):
		return self.Move(p)
	def Pitch(self, p):
		cmd = None
		if 'pitch' in p:
			pitch = p['pitch']
			rule = p['rule'] if 'rule' in p else ''	
			if pitch < 0:
				arg = f'pitch_down(angle={-pitch:0.4f})'
				cmd=f"\t{arg:<54}#'^' : {rule} Pitch"
			elif pitch > 0:
				arg = f'pitch_up(angle={pitch:0.4f})'
				cmd=f"\t{arg:<54}#'&' : {rule} Pitch"
		return cmd	
	def Turn_left(self, p):
		cmd = None
		if 'turn_left' in p:
			turn_left = p['turn_left']
			if turn_left != 0:
				rule = p['rule'] if 'rule' in p else ''	
				arg = f'turn_left(angle={turn_left:0.4f})'
				cmd=f"\t{arg:<54}#'+' : {rule} Turn_left"
		return cmd
	def Tl(self, p):
		return self.Turn_left(p) 
	def Turn_right(self, p):
		cmd = None
		if 'turn_right' in p:
			turn_right = p['turn_right']
			if turn_right != 0:				
				rule = p['rule'] if 'rule' in p else ''	
				arg = f'turn_right(angle={turn_right:0.4f})'
				cmd=f"\t{arg:<54}#'+' : {rule} Turn_right"
		return cmd
	def Tr(self, p):
		return self.Turn_right(p) 
	def Turn(self, p):
		cmd = None
		if 'turn' in p:
			turn = p['turn']
			rule = p['rule'] if 'rule' in p else ''
			if turn > 0:	
				arg = f'turn_left(angle={turn:0.4f})'
				cmd=f"\t{arg:<54}#'+' : {rule} Turn_left"
			elif turn < 0:	
				arg = f'turn_right(angle={-turn:0.4f})'
				cmd=f"\t{arg:<54}#'+' : {rule} Turn_right"
		return cmd
	def Roll(self, p):
		cmd = None
		if 'roll' in p:
			roll = p['roll']
			rule = p['rule'] if 'rule' in p else ''	

			if roll < 0:
				arg = f'roll_right(angle={roll:0.4f})'
				cmd=f"\t{arg:<54}#'/' : {rule} Roll"
			elif roll > 0:
				arg = f'roll_left(angle={roll:0.4f})'
				cmd=f"\t{arg:<54}#'\\' : {rule} Roll"
		return cmd	
			
	def	Object(self, p):
		cmd = None
		if 'object' in p:
			ofile = p['object']	
			
			sx,sy,sz = p['scale'] if 'scale' in p else (1,1,1)
			rule = p['rule'] if 'rule' in p else '??'		

			arg = f'draw_obj("{ofile}", scale=({sx:0.4f},{sy:0.4f},{sz:0.4f}))'
			cmd=f"\t{arg:<54}"f"#'~' : {rule} Object" 
		return cmd		
#-----------------------------------------------------------------------
# Pre-defined ancilliary functions
#
	def Save(self,p):
		#self.L += 1
		arg = f'save()'
		cmd=f"\t{arg:<54}#'[' : save"	
		return cmd
	def Restore(self,p):
		#self.L += 1
		arg = f'restore()'
		cmd=f"\t{arg:<54}#']' : restore"	
		return cmd
	def Prev(self, string):
		""" If the rule following the current rule is string """
		return True
	def Next(self, string):
		""" If the rule following the current rule is string """
		return True
# Dummy routines used in basic rule definitions which are translated to
# actual rule expansion code in same-named object routines.
def Curve(p):		pass
def Draw(p):		pass
def Internode(p):	pass
def Inter(p):		pass
def F(p):			pass
def Move(p):		pass
def f(P):			pass
def Object(p):		pass
def Pitch_down(p):	pass
def Pitch_up(p):	pass
def Pitch(p):		pass
def Turn_left(p):	pass
def Tl(p):			pass
def Turn_right(p):	pass
def Tr(p):			pass
def Turn(p):		pass
def Roll_left(p):	pass
def Roll_right(p):	pass
def Roll(p):		pass
def Save(n):		pass
def Restore(n):		pass

def Prev(p): 		pass
def Next(p): 		pass
translate= {'F': Internode,  'f': Move,
				'+': Turn_left,  '-': Turn_right,
				'&': Pitch_down, '^': Pitch_up, 
				'\\': Roll_left,  '/': Roll_right, 
				'[': Save,		 ']': Restore,
			   }

