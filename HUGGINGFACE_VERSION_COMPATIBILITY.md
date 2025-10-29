# HuggingFace Libraries Version Compatibility

## Issue Resolution: tokenizers Build Error

### Problem
When trying to install `transformers==4.37.2` with `huggingface-hub>=1.0.1`, pip attempted to build tokenizers from source, which failed with:
```
error: can't find Rust compiler
Failed building wheel for tokenizers
```

### Root Cause
**Version Incompatibility:**
- `transformers==4.37.2` requires `huggingface-hub<1.0,>=0.19.3`
- `huggingface-hub>=1.0.1` is incompatible with transformers 4.37.2
- tokenizers attempted to build from source due to version conflicts
- Rust compiler is required to build tokenizers from source

### Solution Applied

**Compatible Version Set:**
```
tokenizers==0.15.2          # Pre-built wheels available
transformers==4.37.2        # Requested stable version
huggingface-hub>=0.20.0,<1.0  # Compatible with transformers 4.37.2
```

### Why This Works

1. **tokenizers==0.15.2**
   - Has pre-built wheels for all architectures (including ARM64)
   - Compatible with transformers 4.37.2
   - No Rust compiler needed

2. **transformers==4.37.2**
   - Stable, well-tested version
   - Full compatibility with sentence-transformers
   - Works perfectly with tokenizers 0.15.2

3. **huggingface-hub 0.x**
   - Compatible with transformers 4.37.2
   - Still has good SSL handling capabilities
   - No build issues

### Alternative: Upgrade Path

If you need huggingface-hub 1.0+ features, you must upgrade to transformers 5.0+:

```
tokenizers>=0.20.0
transformers>=5.0.0
huggingface-hub>=1.0.1
```

**Note:** This requires testing for compatibility with your application.

### Version Compatibility Matrix

| transformers | huggingface-hub | tokenizers | Pre-built Wheels |
|--------------|-----------------|------------|------------------|
| 4.37.2       | 0.20-0.99       | 0.15.2     | ✅ Yes           |
| 4.45+        | 0.20-0.99       | 0.19+      | ✅ Yes           |
| 5.0+         | 1.0+            | 0.20+      | ✅ Yes           |

### Files Modified

1. `/app/backend/requirements.txt`
   - Added: `tokenizers==0.15.2`
   - Added: `transformers==4.37.2`
   - Added: `huggingface-hub>=0.20.0,<1.0`

2. `/app/Dockerfile.backend.artifactory`
   - Removed: huggingface-hub upgrade step (not compatible)
   - Kept: pip/setuptools/wheel upgrade
   - Kept: requests downgrade/upgrade for model downloads

### Verification

**Installed Versions:**
```bash
$ pip list | grep -E "transformers|tokenizers|huggingface-hub"
huggingface-hub    0.36.0
tokenizers         0.15.2
transformers       4.37.2
```

**Backend Status:**
```
✅ Backend starts successfully
✅ sentence-transformers loads models correctly
✅ No build errors
✅ No Rust compiler needed
```

### Build Notes

When building the Docker image:

1. **No Rust Required:**
   - All packages use pre-built wheels
   - Faster build times
   - No additional build dependencies needed

2. **SSL Handling:**
   - Still uses requests 2.27.1 for model downloads
   - huggingface-hub 0.36.0 has good SSL support
   - All SSL environment variables still work

3. **Model Caching:**
   - sentence-transformers downloads successfully
   - Models cached in /root/.cache/huggingface
   - Copied to runtime image as planned

### Common Issues & Solutions

**Issue:** Still getting tokenizers build error
```bash
# Solution: Clear pip cache and rebuild
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

**Issue:** Version conflicts during install
```bash
# Solution: Install in correct order
pip install tokenizers==0.15.2
pip install transformers==4.37.2
pip install huggingface-hub~=0.36.0
```

**Issue:** Deprecation warnings from huggingface_hub
```
FutureWarning: `resume_download` is deprecated...
```
This is non-critical. It will work in version 0.x and the warning can be ignored.

### Performance Impact

✅ **No performance difference** - Pre-built wheels install instantly  
✅ **No runtime difference** - All functionality works the same  
✅ **Faster builds** - No compilation time for tokenizers  
✅ **Smaller image** - No Rust toolchain needed  

---

**Last Updated:** October 29, 2025  
**Status:** ✅ Resolved  
**Backend:** Running successfully with compatible versions
