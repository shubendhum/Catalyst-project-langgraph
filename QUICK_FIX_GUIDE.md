# 🚀 Quick Action Guide - Yarn Install Fix

## Your Issue
```
failed to solve: process "/bin/sh -c yarn install --frozen-lockfile" did not complete
```

## ✅ SOLUTION APPLIED - Ready to Build!

### What Was Fixed
1. **Network timeout** increased to 10 minutes (was 30 seconds)
2. **Build dependencies** added (python3, make, g++, git)
3. **Retry logic** implemented (auto-retry if first attempt fails)
4. **Network concurrency** limited to 1 (more stable)

### 🎯 Try Building Now

**Option 1: Docker Compose (Recommended)**
```bash
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Option 2: Direct Docker Build**
```bash
cd /app/frontend
docker build -f ../Dockerfile.frontend.artifactory -t catalyst-frontend .
```

**Option 3: Test All Methods**
```bash
/app/test-frontend-build.sh
```
This will try 4 different approaches and tell you which one works.

---

## 🔍 If Build Still Fails

### Quick Diagnostics
```bash
# Check files are in place
ls -la /app/frontend/package.json
ls -la /app/frontend/yarn.lock
ls -la /app/frontend/nginx.conf

# Verify Dockerfile has fixes
grep "network-timeout" /app/Dockerfile.frontend.artifactory
# Should show: --network-timeout 600000
```

### Alternative 1: Use Different Dockerfile

**Try Alternative with More Retries**:
```bash
cd /app
# Edit docker-compose.artifactory.yml, change:
# dockerfile: ../Dockerfile.frontend.artifactory
# to:
# dockerfile: ../Dockerfile.frontend.artifactory.alt
docker-compose -f docker-compose.artifactory.yml build frontend
```

**Try Standard Node Image (Public Registry)**:
```bash
cd /app
sed -i 's|dockerfile: ../Dockerfile.frontend.artifactory|dockerfile: ../Dockerfile.frontend.standard|' docker-compose.artifactory.yml
docker-compose -f docker-compose.artifactory.yml build frontend
```

### Alternative 2: Pre-install Dependencies
```bash
# Install on host first
cd /app/frontend
yarn install

# Then build Docker
cd /app
docker-compose -f docker-compose.artifactory.yml build frontend
```

### Alternative 3: Increase Timeout Further
```bash
# Edit /app/Dockerfile.frontend.artifactory
# Change line 24-25 from:
#   --network-timeout 600000
# To:
#   --network-timeout 1200000    # 20 minutes

docker-compose -f docker-compose.artifactory.yml build frontend
```

---

## 📖 Documentation Available

| Document | Purpose |
|----------|---------|
| `YARN_INSTALL_FIX_APPLIED.md` | Details of the fix applied |
| `YARN_INSTALL_TROUBLESHOOTING.md` | Complete troubleshooting guide |
| `ARTIFACTORY_BUILD_FIX.md` | Build context issues (already fixed) |
| `ARTIFACTORY_QUICK_START.md` | Quick reference for Artifactory |

---

## 🛠 Helpful Scripts

```bash
# Apply/reapply fixes
/app/fix-yarn-install.sh

# Test all build methods
/app/test-frontend-build.sh

# Validate file structure
/app/validate-artifactory-build.sh

# Restore original Dockerfile if needed
cp /app/Dockerfile.frontend.artifactory.backup /app/Dockerfile.frontend.artifactory
```

---

## ✅ Success Criteria

You'll know it worked when:
1. Build completes without timeout errors
2. You see: "Successfully built [image-id]"
3. Image appears: `docker images | grep catalyst-frontend`
4. Container runs: `docker run -d -p 8080:80 catalyst-frontend`

---

## 🆘 Still Having Issues?

### Check Common Problems

**Network Issues**:
```bash
# Test if you can reach npm registry
curl -I https://registry.npmjs.org/

# Try with host network
docker build --network=host -f /app/Dockerfile.frontend.artifactory -t test .
```

**Docker Resources**:
- Open Docker Desktop → Settings → Resources
- Ensure Memory: 4GB+
- Ensure CPUs: 2+

**Artifactory Access**:
```bash
# Test Artifactory connection
curl -I https://artifactory.devtools.syd.c1.macquarie.com:9996/

# Login if needed
docker login artifactory.devtools.syd.c1.macquarie.com:9996
```

### Get Detailed Error Info
```bash
# Build with full output
docker-compose -f docker-compose.artifactory.yml build --no-cache --progress=plain frontend 2>&1 | tee build.log

# Check errors
grep -A 10 "error" build.log
grep -A 10 "ERR" build.log
```

---

## 💡 Pro Tips

1. **First time building?** Use `test-frontend-build.sh` to find what works
2. **Behind corporate proxy?** You may need proxy settings
3. **Artifactory slow?** Try standard Node image instead
4. **Local yarn works?** Build context is correct, network issue likely
5. **Still fails?** Share the build.log for specific troubleshooting

---

## 🎯 Most Likely Solutions (in order)

1. ✅ **Already applied** - Enhanced Dockerfile with timeouts and retries
2. 🔄 **Try standard image** - Use public Node registry instead
3. 🔄 **Pre-install locally** - Install dependencies on host first
4. 🔄 **Increase resources** - Give Docker more memory
5. 🔄 **Use alternative Dockerfile** - Try .alt version with more retries

---

## Contact/Support

If none of these work:
1. Check all documentation in `/app/*.md`
2. Review build logs carefully
3. Test network connectivity
4. Verify Docker has adequate resources
5. Try building a simple Node app to isolate the issue

---

**Current Status**: Dockerfile updated with fixes, ready to test build!

**Next Step**: Run `docker-compose -f docker-compose.artifactory.yml build frontend`
