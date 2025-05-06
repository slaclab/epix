[DOE Code](https://www.osti.gov/doecode/biblio/80877)

# Before you clone the GIT repository

1) Create a github account:
> https://github.com/

2) On the Linux machine that you will clone the github from, generate a SSH key (if not already done)
> https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/

3) Add a new SSH key to your GitHub account
> https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/

4) Setup for large filesystems on github
> $ git lfs install

# Clone the GIT repository
```
$ git clone --recursive git@github.com:slaclab/epix
```

# Compile Rogue
```
$ cd epix/software/rogue
```
and follow the instructions in ```README.md```
