cd ~/EdvolutionEmployeePortal

# Make sure you're on the right branch with latest code
git checkout claude/extend-approval-workflow-qcf8s
git pull origin claude/extend-approval-workflow-qcf8s

# Build the Docker image with a new tag
docker build -t us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:rev-$(date +%Y%m%d-%H%M%S) \
             -t us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:latest .

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push both tags (timestamped and latest)
docker push us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:rev-$(date +%Y%m%d-%H%M%S)
docker push us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:latest
