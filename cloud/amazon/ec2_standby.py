#!/usr/bin/python


def get_instances_for_change(asg_name, instance_ids, state):

    if state == "standby":
	state="Standby"
    elif state == "inservice":
	state="InService"

    instance_list = []
    ec2 = boto.ec2.connect_to_region('eu-west-1')
    autoscale = boto.ec2.autoscale.connect_to_region('eu-west-1')
    group = autoscale.get_all_groups(names=[asg_name])[0]

    #instance_ids = [i.instance_id for i in group.instances]
    #instances = ec2.get_only_instances(instance_ids)

    instance_facts = {}
    for i in group.instances:
	instance_facts[i.instance_id] = {'health_status': i.health_status,
                                         'lifecycle_state': i.lifecycle_state,
                                         'launch_config_name': i.launch_config_name }
        if i.lifecycle_state != state and i.instance_id in instance_ids:
		instance_list.append(i.instance_id)
	#	print i.lifecycle_state
	#	print i.instance_id
	else:
		pass
    return instance_list

def enter_or_exit_standby(asg_name,instances,should_decrement,profile,state):

    instances_option=','.join(instances)
    if profile != 'None':
	profile_option="--profile " + profile
    else:
	profile_option=""
    if state == 'standby':
	    if should_decrement:
		decrement_option="--should-decrement-desired-capacity"
	    else:
		decrement_option="--no-should-decrement-desired-capacity"
		# there is no enter-standby in BOTO so I'm using cli until it appears
            cmd = "aws autoscaling enter-standby --instance-ids %s --auto-scaling-group-name %s %s %s" % ( instances_option, asg_name, decrement_option, profile_option )
    elif state == 'inservice':
            cmd = "aws autoscaling exit-standby --instance-ids %s --auto-scaling-group-name %s %s " % ( instances_option, asg_name, profile_option )
    rc = os.system("%s" % cmd)
   
    return rc 

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            instance_ids=dict(required=True, type='list'),
	    profile=dict(type='str', default='None'),
	    should_decrement=dict(type='bool', default=True),
	    state=dict(required=True, choices=['standby', 'inservice']),

        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
	supports_check_mode=False

    )
    if not boto_found:
        module.fail_json(msg="boto is required")

    asg_name = module.params.get('name')
    instance_ids = module.params.get('instance_ids')
    profile = module.params.get('profile')
    should_decrement = module.params.get('should_decrement')
    state = module.params.get('state')
    instances = get_instances_for_change(asg_name, instance_ids, state)

    if len(instances) == 0:
		module.exit_json(changed=False)
    else:
       rc=enter_or_exit_standby(asg_name,instances,should_decrement,profile,state)
       if rc != 0:
          module.fail_json(msg="aws cli command failed")
       else:
          module.exit_json(changed=True)


try:
    import boto.ec2.autoscale
    from boto.ec2.autoscale import AutoScaleConnection, AutoScalingGroup
    from boto.exception import BotoServerError
except ImportError:
    boto_found = False
else:
    boto_found = True

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
