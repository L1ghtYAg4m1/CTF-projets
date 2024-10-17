import torch

def test_cuda():
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"CUDA is available! GPU count: {torch.cuda.device_count()}")
        print(f"GPU name: {torch.cuda.get_device_name(0)}")
        
        # Test if CUDA can be used by performing a simple tensor operation on GPU
        x = torch.tensor([1.0, 2.0, 3.0])
        x = x.to('cuda')
        print(f"Tensor moved to GPU: {x}")
        print(f"Is tensor on CUDA? {x.is_cuda}")
    else:
        print("CUDA is not available. GPU is not being used.")

if __name__ == "__main__":
    test_cuda()
