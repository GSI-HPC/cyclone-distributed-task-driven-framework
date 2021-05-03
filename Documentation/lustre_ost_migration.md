# Lustre OST Migration

Migrate files on Lustre between multiple OSTs to adjust or rebalance its fill state.

## Description

## Configuration

[Configuration File for Task Generator](../Configuration/lustre_ost_migration_task_generator.conf)

### Section: **control**

| Name        | Value  | Description                                      |
| ----------- | ------ | ------------------------------------------------ |
| local\_mode | on/off | Specifies if local or productive mode is enabled |

### Section: **control.local_mode**

| Name        | Value  | Description                                     |
| ----------- | ------ | ----------------------------------------------- |
| num\_osts   | Number | Specifies the number of Lustre OSTs to simulate |

### Section: **control.threshold**

| Name                | Value  | Description                                                                     |
| ------------------- | ------ | ------------------------------------------------------------------------------- |
| update\_fill\_level | Number | Time period in seconds when to update Lustre OSTs fill level                    |
| reload\_files       | Number | Time period in seconds when to reload input files                               |
| print\_caches       | Number | Time period in seconds when to print the caches with number of files to migrate |

### Section: **migration**

| Name                         | Value    | Description                                                                 |
| ---------------------------- | -------- | --------------------------------------------------------------------------- |
| input\_dir                   | Path     | Path to input directory where to process input file lists from              |
| ost\_fill\_threshold\_source | Number   | Lustre OST fill level threshold in percentage for reducing down source OSTs |
| ost\_fill\_threshold\_target | Number   | Lustre OST fill level threshold in percentage for filling up target OSTs    |
| ost\_targets                 | RangeSet | List of decimal OST indexes comma separated and ranges defined with hyphen  |

### Section: **lustre**

| Name      | Value  | Description            |
| --------- | ------ | ---------------------- |
| fs\_path  | Path   | Lustre filesystem path |

## Input File Lists

The input file lists to be processed must be located within the directory specified in the `input_dir` parameter  
of the task generators config file:

```
[migration]
input_dir = ...
```
