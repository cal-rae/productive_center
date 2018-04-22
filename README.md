# This contains the model for the original productive center scheduling. Uses python 3.x

# Run productive_center_LP.py (~9 minutes on a 2014 Macbook). If you want to vary the parameters, you should use the
# prob object and modify the constraints/parameters to reduce computation time. The problem takes 6 seconds on the same
# machine because most of the time is cvxpy taking the code and turning it into a formal problem for the solver to use.

# The rest of the files either generate test data or store results. It's a bit of a mess in that area. The matlab files
# were Steven Percy's data generation files.

# The requirements file is not included because it contained a bunch of extra junk because I had the xlsx and m files