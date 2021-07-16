# stdglue - canned prolog and epilog functions for the remappable builtin codes (T,M6,M61,S,F)
#
# we dont use argspec to avoid the generic error message of the argspec prolog and give more
# concise ones here

# cycle_prolog,cycle_epilog: generic code-independent support glue for oword sub cycles
#
# these are provided as starting point - for more concise error message you would better
# write a prolog specific for the code
#

import emccanon 
from interpreter import *
throw_exceptions = 1

# REMAP=M6  modalgroup=6 prolog=change_prolog ngc=change epilog=change_epilog
# exposed parameters:
#    #<tool_in_spindle>
#    #<selected_tool>
#    #<current_pocket>
#    #<selected_pocket>

def change_prolog(self, **words):
    try:
        if self.selected_pocket < 0:
            self.set_errormsg("M6: no tool prepared")
            return INTERP_ERROR

        if self.cutter_comp_side:
            self.set_errormsg("Cannot change tools with cutter radius compensation on")
            return INTERP_ERROR

        self.params["tool_in_spindle"] = self.current_tool
        self.params["selected_tool"] = self.selected_tool
        self.params["current_pocket"] = self.current_pocket
        self.params["selected_pocket"] = self.selected_pocket
        return INTERP_OK

    except Exception as e:
        self.set_errormsg("M6/change_prolog: %s" % (e))
        return INTERP_ERROR

def change_epilog(self, **words):
    try:
        if not self.value_returned:
            r = self.blocks[self.remap_level].executing_remap
            self.set_errormsg("the %s remap procedure %s did not return a value"
                             % (r.name,r.remap_ngc if r.remap_ngc else r.remap_py))
            yield INTERP_ERROR
 
        if self.blocks[self.remap_level].builtin_used:
            #print "---------- M6 builtin recursion, nothing to do"
            yield INTERP_OK
        else:
            if self.return_value > 0.0:
                # commit change
                self.selected_pocket =  int(self.params["selected_pocket"])
                emccanon.CHANGE_TOOL(self.selected_pocket)
                self.current_pocket = self.selected_pocket
                self.selected_pocket = -1
                self.selected_tool = -1
                # cause a sync()
                self.set_tool_parameters()
                self.toolchange_flag = True
                yield INTERP_EXECUTE_FINISH
            else:
                message = "Error in Tool change routine\n"
                if self.return_value == -100:
                    # Unknown tool in spindle
                    message += "Unknown tool in spindle"
                elif self.return_value == -101:
                    # Shuttle not in park position
                    message += "Shuttle not in park position"
                elif self.return_value == -102:
                    # Tool clamp status switch not active
                    message += "Tool clamp status switch not active"
                else:
                    message = "M6 aborted (return code {0})".format(self.return_value)
                self.set_errormsg(message)         
                yield INTERP_ERROR

    except Exception as e:
        self.set_errormsg("M6/change_epilog: %s" % (e))
        yield INTERP_ERROR

# this should be called from TOPLEVEL __init__()
def init_stdglue(self):
    self.sticky_params = dict()
