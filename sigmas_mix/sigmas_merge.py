import torch
from copy import deepcopy
class sigmas_merge:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas_1": ("SIGMAS", {"forceInput": True}),
                "sigmas_2": ("SIGMAS", {"forceInput": True}),
                "proportion_1": ("FLOAT", {"default": 0.5, "min": 0,"max": 1,"step": 0.01})
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/sigmas"
    
    def simple_output(self, sigmas_1, sigmas_2, proportion_1):
        return (sigmas_1*proportion_1+sigmas_2*(1-proportion_1),)
 
class sigmas_mult:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas": ("SIGMAS", {"forceInput": True}),
                "factor": ("FLOAT", {"default": 1, "min": 0,"max": 2,"step": 0.01})
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/sigmas"
    
    def simple_output(self, sigmas, factor):
        return (sigmas*factor,)
    
class sigmas_concat:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas_1": ("SIGMAS", {"forceInput": True}),
                "sigmas_2": ("SIGMAS", {"forceInput": True}),
                "sigmas_1_until": ("INT", {"default": 10, "min": 0,"max": 1000,"step": 1}),
                "rescale_sum" : ("BOOLEAN", {"default": True}),
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/sigmas"
    
    def simple_output(self, sigmas_1, sigmas_2, sigmas_1_until,rescale_sum):
        result = torch.cat((sigmas_1[:sigmas_1_until], sigmas_2[sigmas_1_until:]))
        if rescale_sum:
            result = result*torch.sum(result).item()/torch.sum(sigmas_1).item()
        return (result,)
    
    
class the_golden_scheduler:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "steps": ("INT", {"default": 20, "min": 0,"max": 100000,"step": 1}),
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/schedulers"
    
    def simple_output(self,model,steps):
        s = model.model.model_sampling
        sigmin = s.sigma(s.timestep(s.sigma_min))
        sigmax = s.sigma(s.timestep(s.sigma_max))
        
        phi = (1 + 5 ** 0.5) / 2
        sigmas = torch.tensor([(1-x/(steps-1))**phi*(sigmax-sigmin)+sigmin for x in range(steps)]+[0]).cuda()
        return (sigmas,)

def remap_range_no_clamp(value, minIn, MaxIn, minOut, maxOut):
            finalValue = ((value - minIn) / (MaxIn - minIn)) * (maxOut - minOut) + minOut;
            return finalValue;

class get_sigma_float:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "sigmas": ("SIGMAS", {"forceInput": True}),
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("FLOAT",)
    CATEGORY = "sampling/custom_sampling/sigmas"
    
    def simple_output(self,sigmas,model):
        sigfloat = float((sigmas[0]-sigmas[-1])/model.model.latent_format.scale_factor)
        return (sigfloat,)

def remap_range_no_clamp(value, minIn, MaxIn, minOut, maxOut):
            finalValue = ((value - minIn) / (MaxIn - minIn)) * (maxOut - minOut) + minOut;
            return finalValue;

class sigmas_gradual_merge:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "sigmas_1": ("SIGMAS", {"forceInput": True}),
                "sigmas_2": ("SIGMAS", {"forceInput": True}),
                "proportion_1": ("FLOAT", {"default": 0.5, "min": 0,"max": 1,"step": 0.01})
            }
        }

    FUNCTION = "simple_output"
    RETURN_TYPES = ("SIGMAS",)
    CATEGORY = "sampling/custom_sampling/sigmas"
    
    def simple_output(self,sigmas_1,sigmas_2,proportion_1):
        result_sigmas = deepcopy(sigmas_1)
        for idx,s in enumerate(result_sigmas):
            current_factor = remap_range_no_clamp(idx,0,len(result_sigmas)-1,proportion_1,1-proportion_1)
            result_sigmas[idx] = sigmas_1[idx]*current_factor+sigmas_2[idx]*(1-current_factor)
        result_sigmas = result_sigmas.cuda()        
        return (result_sigmas,)
    
NODE_CLASS_MAPPINGS = {
    "Merge sigmas by average": sigmas_merge,
    "Merge sigmas gradually": sigmas_gradual_merge,
    "Multiply sigmas": sigmas_mult,
    "Split and concatenate sigmas": sigmas_concat,
    "The Golden Scheduler": the_golden_scheduler,
    "Get sigmas as float": get_sigma_float,
    
}
