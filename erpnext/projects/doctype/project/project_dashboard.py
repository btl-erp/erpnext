from frappe import _
'''
--------------------------------------------------------------------------------------------------------------------------
Version          Author          CreatedOn          ModifiedOn          Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		  SHIV		                    15/08/2017         Introducting BOQ
--------------------------------------------------------------------------------------------------------------------------                                                                          
'''

'''
data = {
	'heatmap': True,
	'heatmap_message': _('This is based on the Time Sheets created against this project'),
	'fieldname': 'project',
	'transactions': [
		{
			'label': _('Project'),
                        'items': ['Task', 'Timesheet', 'BOQ', 'Issue', 'MB Entry']
		},
                {
			'label': _('Transactions'),
			'items': ['Project Advance', 'Project Invoice', 'Project Payment']
		},
		{
			'label': _('Material'),
			'items': ['Material Request', 'BOM', 'Stock Entry']
		},
	]
}
'''

data = {
	'heatmap': True,
	'heatmap_message': _('This is based on the Time Sheets created against this project'),
	'fieldname': 'project',
	'transactions': [
		{
			'label': _('Work Progress'),
                        'items': ['Task', 'Timesheet']
		},
                {
			'label': _('BOQ & SUBCONTRACT'),
                        'items': ['BOQ', 'BOQ Adjustment', 'Subcontract', 'MB Entry']
		},
                {
			'label': _('Transactions'),
			'items': ['Project Advance', 'Project Invoice', 'Project Payment']
		},
		{
			'label': _('Material'),
			'items': ['Material Request', 'Stock Entry']
		},
	]
}
