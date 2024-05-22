## Git Basics: Push and Pull Requests

Here's a step-by-step guide on managing the Printer Playgound repository on GitHub. I'l cover the Branch structure, pulls requests, merging, and a few other things. This is a living document and will be updated as needed.

First, let's set up a basic branch structure for the repository. This will help us manage the development process and keep the codebase stable. I broke it into three branch types: Main, Development, and Feature. Here's an overview of each:

### Branches

1. <b>Main Branch</b> - The default branch with the current stable codebase. It's the stable version of the codebase and should only contain production-ready code.
2. <b>Development Branch</b> - The branch where new features are developed and tested.
3. <b>Feature Branch</b> - A branch created from the development branch to work on a specific feature or bug fix.

This allows up to work on new features without affecting the main codebase. Once the feature is complete and tested, it can be merged into the development branch. If it's easier, each contributor can create their own feature branch to work on a specific feature or bug fix.

### Pull Requests

Once the code on your feature branch is ready, you can push to GitHub and then create a pull request to merge it with the development branch.

This is done using a pull request tab in the top menu on the GitHub site. Here's a step-by-step guide on how to do this:

1. Push your feature branch to the repository on GitHub.
2. Go to the repository on GitHub and click on the "Pull Requests" tab.
3. Click on the "New Pull Request" button.
4. Select the development branch as the base branch and your feature branch as the compare branch.
5. Review the changes and click on the "Create Pull Request" button.
6. Add a title and description to your pull request and click on the "Create Pull Request" button.

Once the pull request is created, we can can review the changes and leave comments if anything needs to be changed. If everything looks good, the pull request can be merged (review to follow) into the development branch. This will integrate the new feature into the codebase and make it available for testing.

### Merging

Merging a pull request is a simple process. Once the changes have been reviewed and approved, you can merge the pull request into the development branch. Here's a step-by-step guide on how to do this:

1. Go to the repository on GitHub and click on the "Pull Requests" tab.
2. Click on the pull request you want to merge.
3. Review the changes and leave comments if needed.
4. Click on the "Merge Pull Request" button.

Once the development branch has been tested and is ready for production, it can be merged into the main branch.

This is the same process as the feature branch, but the base branch is the main branch and the compare branch is the development branch. Once the pull request is merged, the new code will be available.

### Testing

To create tests on GitHub you can use the "Actions" tab. This allows you to create automated tests that run when a pull request is created. I'll go over it in more detail in a future update after we discuss specific testing needs.
