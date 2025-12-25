# Testing for patchtools, using pyunit

## What to test -- Which Scripts do we actually test?

These unit test just call the "exportpatch" or "fixpatch" scripts. This
means that the first binary in your path, when running the tests, will
be the binary that is tested.

This allows these tests to be run on any installed version of patchtools,
so they can be run against older versions, current version, or proposed
versions of the tools, as desired. So be sure the scripts being
tested are the ones you expect to be tested, by running something
like "which exportpatch".

## Things to test

### exportpatch

#### error conditions

* bogus commit supplied (does not match anything)
* no commit supplied
* try to supply "HEAD" or "^" (should fail)
* incorrect patch config file (points to nothing?)
* no patch config file?
* try to write with no write permission in dir
* invalid directory supplied to write patch
* specify out-of-range starting number for a numbered patch
* trying to write a patch file when one already exists without --force (should get funky name)

* test with various (or missing) config file for what RFEPOs to search


#### normal ops

NOTE: how to control what the patch config file(s) is/are? Should we
set our own, since we are testing? I think we should know what they
are, for testing.

* export a simple commit, just one file, just one hunk:

** export to a dir/file, using defaults                     -- done (2 cases)
   repeat with a suffix

** export to a dir/file, using numeric values,              -- done (3 cases)
   repeat with non-default starting number
   repeat with non-default width

** export to a dir/file, using 'force' to overwrite         -- done (2 cases)
   repeat without force set

** export to stdout                                         -- done (1 case)

** export to current dir                                    -- done (1 case)

** export to dir/file, testing reference                    -- done (1 case)

** export to dir/file, using 'signed-off-by'                -- NOT DONE YET!
   (how to know how it will be "signed off by"?)


* extract testing

** export to file, extract whole (single) file              -- done (5 cases)
   repeat with two files
   repeat with specified file not in patch w/one file
   repeat with specified file not in patch w/two files
   repeat with one of two files in patch specified

* exclude testing


* export a tag (not a commit)


* test various commits to ensure "Patch-mainline" is correct


### error ops

* test "num-width" limits

* test bogus params, such as
** bogus commit
** no commit
** bad arguments
** illegal values for num-width?

## How to Test

To run these tests, using the python unittest module. For
example, from the source directory, you can run:

    zsh> python3.11 -m unittest -v test

If you can find/load the "pytest" command, it's a little
nicer, and be run like:

    zsh> pytest-3.11 -v test

This will run all the tests in the "test" class, which
are int he "test" subdirectory. To run a single test, you
could use:

    zsh> pytest-3.11 -v test.test_exportpatch.TestExportpatchNormalFunctionality.test_to_stdout_defaults
