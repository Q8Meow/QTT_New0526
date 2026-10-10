#!/usr/bin/env python3
from __future__ import annotations
_ORDINARY_INITIALIZED_MODULE_CODE_V1 = __import__("sys")._getframe().f_code
# QTT_ORDINARY_NATIVE_C_DATA_BEGIN_20261008_V1
_QTT_ORDINARY_NATIVE_C_SOURCE_V1 = rb'''/* Source-only private component of the existing workflow Bash owner.
 * This file has not been compiled, loaded or run.  The original qualified
 * Bash's genuine selected installation/ABI must qualify these fixed declarations.
 * It creates no application executor, network client, registry or wire field.
 */
#define _GNU_SOURCE 1
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <stdatomic.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/sysmacros.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <linux/fs.h>
#include <linux/magic.h>
#include <linux/nsfs.h>
#include <linux/close_range.h>
#include <sched.h>
#include <poll.h>
#include <signal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/statvfs.h>
#include <sys/xattr.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Exact minimal GNU Bash 5.2 exported ABI projection: command.h WORD_DESC /
 * WORD_LIST, builtins.h struct builtin, variables.h SHELL_VAR, and general.h
 * sh_builtin_func_t / load / void unload. Complete original reference bytes
 * were independently retained; they are NOT installed-runtime certification.
 * Only the original qualified Linux x86-64 LP64 Bash 5.2 selection may load
 * this component. No header installation or generated config.h is needed.
 */
#if !defined(__x86_64__) || !defined(QN_SOURCE_BASH_VERSION)
#error The actual selected Bash 5.2 Linux x86-64 ABI binding is required.
#endif
typedef struct word_desc { char *word; int flags; } WORD_DESC; typedef struct word_list { struct word_list *next; WORD_DESC *word; } WORD_LIST; typedef struct variable SHELL_VAR; struct variable { char *name,*value,*exportstr; SHELL_VAR *(*dynamic_value)(SHELL_VAR *); SHELL_VAR *(*assign_func)(SHELL_VAR *,char *,intmax_t,char *); int attributes,context; }; struct builtin { char *name; int (*function)(WORD_LIST *); int flags; char *const *long_doc; const char *short_doc; char *handle; }; extern SHELL_VAR *find_variable_noref(const char *); extern SHELL_VAR *bind_variable(const char *,char *,int);
#define BUILTIN_ENABLED 0x01
#define exported_p(v) ((v)->attributes&0x0000001)
#define readonly_p(v) ((v)->attributes&0x0000002)
#define array_p(v) ((v)->attributes&0x0000004)
#define assoc_p(v) ((v)->attributes&0x0000040)
#define nameref_p(v) ((v)->attributes&0x0000800)
#define value_cell(v) ((v)->value)
_Static_assert(sizeof(void *)==8 && sizeof(long)==8 && sizeof(int)==4,"Selected LP64 ABI"); _Static_assert(sizeof(WORD_DESC)==16 && sizeof(WORD_LIST)==16,"Selected word ABI"); _Static_assert(sizeof(SHELL_VAR)==48 && offsetof(SHELL_VAR,attributes)==40,"Selected variable ABI"); _Static_assert(sizeof(struct builtin)==48 && offsetof(struct builtin,long_doc)==24,"Selected builtin ABI");
#if !defined(__linux__) || !defined(SYS_pidfd_open) || !defined(SYS_gettid)
#error The independently selected Linux native and pidfd ABI is required.
#endif
#if !defined(SYS_close_range) || !defined(CLOSE_RANGE_CLOEXEC) || \
    !defined(NS_GET_NSTYPE) || !defined(CLONE_NEWCGROUP) || !defined(CLONE_NEWNS)
#error Original private child descriptor table and exact namespace type ABI are required.
#endif
#if !defined(O_NOFOLLOW) || !defined(O_CLOEXEC) || !defined(AT_SYMLINK_NOFOLLOW)
#error Original no-follow and close-on-exec operations are required.
#endif

/* These bounds are fixed implementation storage, not resource permission.
 * Actual selected Source demands and the original shared ledgers must fit
 * BEFORE any load or operation.  Exhaustion never refunds prior acquisitions.
 */ _Static_assert(sizeof(pid_t)==4 && INT_MAX==2147483647 && (pid_t)-1<0,
  "Original private PARENT programme requires the selected signed32 PID domain");
#define QN_CHUNK 65536U
#if !defined(QN_SOURCE_NATIVE_SLOT_COUNT) || !defined(QN_SOURCE_INPUT_COUNT) || \
    !defined(QN_SOURCE_COMMAND_COUNT)
#error Exact original Source-selected startup catalogue and all-outcome slot counts are required.
#endif
#if QN_SOURCE_NATIVE_SLOT_COUNT < 1
#error Exact Source-selected all-outcome slot storage must be admitted before build.
#endif
#if QN_SOURCE_INPUT_COUNT < 1 || QN_SOURCE_INPUT_COUNT > 120000
#error Exact startup input count is required and must fit the original file ceiling.
#endif
#define QN_SLOTS QN_SOURCE_NATIVE_SLOT_COUNT
#define QN_INPUTS QN_SOURCE_INPUT_COUNT
#if !defined(QN_SOURCE_CATALOGUE_COUNT) || !defined(QN_SOURCE_ABSENCE_COUNT)
#error Complete original startup directory and absence catalogue counts are required.
#endif
#if QN_SOURCE_CATALOGUE_COUNT < 0 || QN_SOURCE_CATALOGUE_COUNT > 20000 || \
    QN_SOURCE_ABSENCE_COUNT < 0 || QN_SOURCE_ABSENCE_COUNT > 120000
#error Startup catalogue must fit the original file and directory ceilings.
#endif
#if QN_SOURCE_COMMAND_COUNT < 9 || QN_SOURCE_COMMAND_COUNT > 65536
#error Exact all-outcome original native command count must fit its programme.
#endif
/* The original command roster remains 0/1 COMMON, 2..7 suffix and 8 launcher.
 * Input/catalogue seal/restore each has its original four fixed occurrences.
 * Two separate ancestor timestamp readbacks follow that complete finite roster.
 */
#define QN_ANCESTOR_ORIGIN_BEFORE (9U+4U*QN_SOURCE_INPUT_COUNT+4U*QN_SOURCE_CATALOGUE_COUNT)
#define QN_ANCESTOR_ORIGIN_AFTER (QN_ANCESTOR_ORIGIN_BEFORE+1U)
#if QN_SOURCE_COMMAND_COUNT != (16U+4U*QN_SOURCE_INPUT_COUNT+4U*QN_SOURCE_CATALOGUE_COUNT)
#error Original complete command storage must include both ancestor readbacks and all three gated-child manager occurrences.
#endif
#define QN_BORROWS 4U
#define QN_ERRORS 128U
#define QN_PATH 4096U
#define QN_DATA 1048576U
#define QN_CGROUP_ROOT "/sys/fs/cgroup"
#define QN_WHOLE_MEMORY UINT64_C(4294967296)
#define QN_WHOLE_TASKS UINT64_C(256)
#define QN_CPU_QUOTA UINT64_C(200000)
#define QN_CPU_PERIOD UINT64_C(100000)
#define QN_DURATION UINT64_C(3720000000000)
#ifndef QN_SOURCE_RETAINED_HEAP_BYTES
#error Original selected native preparation retained-heap allocation is required before build.
#endif
#ifndef QN_SOURCE_REALLOC_ATTEMPT_BYTES
#error Separate prefunded transient old/new reallocation attempt extent is required.
#endif
#if !defined(QN_SOURCE_INSTALLATION_ROOT) || !defined(QN_SOURCE_WORKSPACE) || \
    !defined(QN_SOURCE_SNAPSHOT_ROOT) || !defined(QN_SOURCE_STORAGE_BYTES) || \
    !defined(QN_SOURCE_WRITE_BYTES) || !defined(QN_SOURCE_ALIAS_COUNT)
#error Actual original installation/workspace/private backing and prefunded Source bounds are required.
#endif
#if !defined(QN_SOURCE_CALLS) || !defined(QN_SOURCE_READ_BYTES) || !defined(QN_SOURCE_METADATA_CALLS)
#error Fixed independently selected whole preparation programme allowances are required before build.
#endif

/* PRIVATE original precompiler Source DATA. The original reviewed preparer
 * must acquire these five facts from the create-new selected store BEFORE
 * compilation, retain that actual directory/protection generation through
 * every user, and supply the fixed compiler input. These constants do not
 * create that producer or certify its lifetime. No current C stat fills them.
 * No public builtin argument, environment entry, receipt schema or new file
 * transports them. Missing genuine operands are an explicit compile denial.
 */
#if !defined(QN_SOURCE_SNAPSHOT_PRIOR_DEV) || !defined(QN_SOURCE_SNAPSHOT_PRIOR_INO) || \
    !defined(QN_SOURCE_SNAPSHOT_PRIOR_MODE) || !defined(QN_SOURCE_SNAPSHOT_PRIOR_UID) || \
    !defined(QN_SOURCE_SNAPSHOT_PRIOR_GID)
#error Original precompiler create-new root DATA and its retained owner/protected Source/compiler input association are required.
#endif
struct qn_prior_snapshot_root { uintmax_t dev,ino,mode,uid,gid; }; static const struct qn_prior_snapshot_root qn_prior_snapshot_root = { (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_DEV, (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_INO, (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_MODE, (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_UID, (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_GID }; _Static_assert((uintmax_t)(dev_t)QN_SOURCE_SNAPSHOT_PRIOR_DEV == (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_DEV,"Original root dev_t range"); _Static_assert((uintmax_t)(ino_t)QN_SOURCE_SNAPSHOT_PRIOR_INO == (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_INO,"Original root ino_t range"); _Static_assert((uintmax_t)(mode_t)QN_SOURCE_SNAPSHOT_PRIOR_MODE == (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_MODE,"Original root mode_t range"); _Static_assert((uintmax_t)(uid_t)QN_SOURCE_SNAPSHOT_PRIOR_UID == (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_UID,"Original root uid_t range"); _Static_assert((uintmax_t)(gid_t)QN_SOURCE_SNAPSHOT_PRIOR_GID == (uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_GID,"Original root gid_t range"); _Static_assert((uintmax_t)QN_SOURCE_SNAPSHOT_PRIOR_MODE == (uintmax_t)(S_IFDIR|0700),
               "Original private root exact directory mode");  enum qn_stage { QN_ZERO, QN_PREPARING, QN_PREBIRTH, QN_RUNNING, QN_TERMINAL, QN_RETIRED, QN_CLOSED, QN_HELD }; enum qn_role { QN_CHECKER, QN_PROVISION, QN_PARENT, QN_RECEIVER }; struct qn_version { dev_t dev; ino_t ino; mode_t mode; nlink_t links; off_t size; struct timespec mtime, ctime; }; struct qn_slot { int registered, fd, close_attempted, close_result, close_errno; int parent; char component[NAME_MAX + 1]; struct qn_version path_before, handle_before; }; struct qn_error { char operation[64]; int native_errno; uint64_t ordinal; };
/* Only the original ephemeral C backings receive this readonly loan.
 * No installed/source file mode or owner is changed. Before/returned/protected
 * and terminal versions stay distinct in this SAME original keeper journal. */ struct qn_startup_mode_loan { int registered,grant_admission,grant_dispatched,grant_returned,grant_checked; int sealed,restore_admission,restore_dispatched,restore_returned,restored; int grant_slot,grant_errno,restore_errno; uid_t uid; gid_t gid; unsigned long original_flags,protected_flags; struct qn_version before_path,before_handle,granted_path,granted_handle; struct qn_version protected_path,protected_handle; struct qn_version restore_before_path,restore_before_handle,restored_path,restored_handle; }; struct qn_input { int occupied, source_slot, snapshot_slot; char source[QN_PATH], snapshot[QN_PATH]; struct qn_version source_version, snapshot_version; struct qn_version protected_source_path,protected_source_handle; struct qn_version protected_baseline_path,protected_baseline_handle; uint64_t length; unsigned long flags,baseline_flags; unsigned long original_flags,baseline_original_flags; int source_seal_attempted,baseline_seal_attempted; int source_restore_attempted,baseline_restore_attempted; struct qn_startup_mode_loan startup_baseline_loan; };
/* Original per-occurrence gate and terminal observations. These are retained
 * Source/native DATA, never a transferred grant or a successful-receipt flag.
 */ struct qn_gate_write { int registered,reserved; int pending_attempted,pending_result,pending_errno,preexisting_pending; int install_attempted,install_result,install_errno,prior_valid; int write_attempted,write_errno; ssize_t write_result; int restore_attempted,restore_result,restore_errno; sigset_t pending; struct sigaction prior_action; }; struct qn_terminal_observation { int registered,native_attempted,result,native_errno; siginfo_t info; }; struct qn_borrow { int registered, returned, pid_slot; pid_t pid; uint64_t start_ticks; int terminal_code, terminal_status; struct qn_terminal_observation return_observation; }; struct qn_command { int registered, pending, child_created, exec_proven, terminal; int stdout_eof, stderr_eof, status, pid_slot, stdout_slot, stderr_slot; pid_t pid; uint64_t start_ns, end_ns, start_ticks; size_t stdout_used, stderr_used; char *stdout_data, *stderr_data; unsigned char exec_failure_raw[sizeof(int)+1]; size_t exec_failure_bytes; int exec_eof,exec_failure_errno; struct qn_gate_write gate_write; struct qn_terminal_observation terminal_observation; }; struct qn_catalogue { int registered,directory_slot,baseline_slot,seal_attempted,restore_attempted; unsigned long original_flags,flags,baseline_original_flags,baseline_flags; struct qn_version original_path,original_handle,baseline_path,baseline_handle; char directory[QN_PATH],baseline[QN_PATH]; char *names; size_t names_length,name_count; struct qn_startup_mode_loan startup_baseline_loan; }; struct qn_absence { int registered,parent_slot; char component[NAME_MAX+1]; struct qn_version parent_path,parent_handle; }; struct qn_alias { int registered,parent_slot; char path[QN_PATH],name[NAME_MAX+1],target[QN_PATH]; struct qn_version original; size_t length; };
/* PRIVATE existing-owner direct PROVISION continuation. These command
 * incidences follow every existing SourceSeal input/catalogue incidence;
 * original common0/1, retirement2..7 and PROVISION8 keep their identities.
 * The exact existing QN_SOURCE_COMMAND_COUNT must include these two origin plus three gated-continuation rows.
 */
#define QN_PROVISION_STREAM UINT64_C(8388608)
#define QN_PROVISION_COMBINED UINT64_C(16777216)
/* BASE and BASE+1 belong to the separately authored original ancestor-clock readbacks. */
#define QN_PRIVATE_COMMAND_BASE (9U+4U*QN_INPUTS+4U*QN_SOURCE_CATALOGUE_COUNT)
#define QN_SCOPE_CREATE (QN_PRIVATE_COMMAND_BASE+2U)
#define QN_SCOPE_BEFORE (QN_PRIVATE_COMMAND_BASE+3U)
#define QN_SCOPE_RELEASE (QN_PRIVATE_COMMAND_BASE+4U)
#if QN_SOURCE_COMMAND_COUNT < QN_PRIVATE_COMMAND_BASE+7U
#error Original all-outcome Source command storage must include the two origin, three gated-continuation and two private parser rows.
#endif
/* PRIVATE original keeper observations. Only the three role entries cross
 * the genuine gated PROVISION exec. FD values are actor-local journal DATA,
 * never argv, environment, wire authority or a new public builtin. The same
 * original Bash remains inside its synchronous native continuation: no exec
 * may replace the maps handle's original mm while this loan is in use. */
enum qn_keeper_observation_role {
  QN_KEEPER_CGROUP_NAMESPACE, QN_KEEPER_MOUNT_NAMESPACE, QN_KEEPER_MAPS
};
struct qn_keeper_check {
  int registered,stat_returned,poll_attempted,poll_result,poll_errno;
  short poll_revents;
  uint64_t start_ticks;
};
struct qn_keeper_observation_loan {
  int attempted,prepared,retirement_attempted,retired;
  int partial_close_attempted,partial_close_result;
  int role,process_slot,stat_slot,namespace_slot,keeper_pid_slot;
  int observation_slots[3];
  pid_t keeper_pid;
  uint64_t keeper_start,origin_ns,cutoff_ns;
  const void *source_owner;
  uint64_t source_input_count,source_catalogue_count,source_alias_count;
  struct qn_version namespace_links[2];
  uid_t observed_uid[3]; gid_t observed_gid[3];
  int namespace_types[2],descriptor_flags[3],access_flags[3];
  off_t maps_initial_offset;
  struct qn_keeper_check keeper_checks[4];
};
struct qn_prefix_journal;
struct qn_provision { int attempted, prepared, mask_held, scope_attempted, bound; int release_attempted, released, observed, return_attempted; int receipt_attempted,receipt_decoded,receipt_parent_status; pid_t receipt_parent_pid; size_t receipt_offset,receipt_length; int reap_attempted, reaped, exec_done, exec_errno; int out_writer,err_writer,gate_reader,gate_writer,exec_reader,exec_writer; int image_slot,null_slot; size_t exec_used,environment_count; uid_t selected_uid; gid_t selected_gid; sigset_t original_mask; char *environment[26]; char image[QN_PATH],script[QN_PATH],bootstrap_invocation[33]; int root_parent,root_slots[3],root_attempted[3],root_created[3]; char root_name[65]; struct qn_prefix_journal *prefix_journal; size_t prefix_bytes;
  int prefix_map_attempted,prefix_merged,prefix_unmap_attempted;
  struct qn_keeper_observation_loan keeper_observations;
};
/* PRIVATE Source constants selected by the original pre-build owner. Policy/config/features/output paths
 * are DATA under the same selected QN_SOURCE_SNAPSHOT_ROOT. Workflow, original
 * Bash controller, native C and native SO are exact original Source operands. No builtin argument,
 * environment marker or field in QTT JSON supplies these values. */
#if !defined(QN_SOURCE_POLICY_BASE) || !defined(QN_SOURCE_POLICY_CONFIG) || \
    !defined(QN_SOURCE_POLICY_FEATURES) || !defined(QN_SOURCE_POLICY_OUTPUT_ROOT) || \
    !defined(QN_SOURCE_APPARMOR_PARSER) || \
    !defined(QN_SOURCE_WORKFLOW_PATH) || !defined(QN_SOURCE_BASH_CONTROLLER_PATH) || \
    !defined(QN_SOURCE_NATIVE_C_PATH) || !defined(QN_SOURCE_NATIVE_SO_PATH)
#error Original pre-build workflow/Bash/native C/SO/policy/config/features/output/parser Source selection is required.
#endif
#define QN_POLICY_COMPILE (QN_PRIVATE_COMMAND_BASE+5U)
#define QN_POLICY_REPLACE (QN_PRIVATE_COMMAND_BASE+6U)
/* Existing nonlauncher capture denies an individual stream above QN_CHUNK.
 * This policy profile explicitly retains that denial; no larger buffer grant. */
#define QN_POLICY_BINARY_LIMIT QN_CHUNK
struct qn_policy_flag_effect { int attempted,returned,native_errno,generation_retained; uid_t uid; gid_t gid; struct qn_version before_path,before_handle; }; struct qn_policy_transition { int attempted,source_slot,binary_slot,output_root_slot; int source_protect_attempted,binary_protect_attempted; unsigned long source_original_flags,binary_original_flags; int compiled,replace_attempted,replaced,checked; int source_restore_attempted,binary_restore_attempted,retirement_attempted,retired; int partial_cleanup_attempted,partial_cleanup_active,partial_cleanup_complete,partial_cleanup_refusal; uint64_t slots_begin; struct qn_policy_flag_effect source_flag_effect,binary_flag_effect; char root[QN_PATH],source[QN_PATH],binary[QN_PATH]; char *body; size_t body_bytes; };  struct qn_owner { int entry_attempted; enum qn_stage stage; pid_t pid, tid; uint64_t origin_ns, cutoff_ns, calls_remaining, read_remaining; uint64_t metadata_remaining, read_bytes, metadata_calls, syscall_calls; uint64_t heap_remaining; uint64_t realloc_peak_remaining; uint64_t write_remaining,write_bytes,largest_write,payload_bytes,roster_bytes; uint64_t largest_read, errors_used, slots_used, input_count; uint64_t catalogue_count,absence_count; int catalogue_complete; int catalogue_attempted,snapshot_root_slot; int snapshot_root_adopt_attempted,snapshot_root_adopt_slot; uint64_t snapshot_root_adopt_slots_begin; uint64_t alias_count; int root_slot, ancestor_slot, common_slot, bootstrap_slot, proc_slot; int common_attempted; char ancestor_group[160]; int prefix_unmounted, six_calls, first_error, scope_started; int command_occurrence, bootstrap_present, common_present; char stem[65], common[65], bootstrap[65]; char invocation[33]; char manager_boot[37]; char phase[64]; struct qn_provision provision; struct qn_policy_transition controller_policy; struct qn_startup_mode_loan startup_root_loan; struct qn_slot slots[QN_SLOTS]; struct qn_input inputs[QN_INPUTS]; struct qn_borrow borrows[QN_BORROWS]; struct qn_error errors[QN_ERRORS];
  struct qn_command commands[QN_SOURCE_COMMAND_COUNT]; struct qn_catalogue catalogues[QN_SOURCE_CATALOGUE_COUNT+1]; struct qn_absence absences[QN_SOURCE_ABSENCE_COUNT+1]; struct qn_alias aliases[QN_SOURCE_ALIAS_COUNT+1]; };
/* SAME original supported Linux x86-64 LP64 compiler/header association.
 * These compile predicates precede loader/init. They are not later native
 * observations, Windows sizeof values or new serialized compiler authority. */ _Static_assert(sizeof(pid_t)==4 && (pid_t)-1<0 && INT_MAX==2147483647,
               "Original supported signed pid_t/int"); _Static_assert(sizeof(dev_t)==8 && sizeof(ino_t)==8 && sizeof(mode_t)==4 && sizeof(nlink_t)==8 && sizeof(off_t)==8 && sizeof(time_t)==8 && sizeof(uid_t)==4 && sizeof(gid_t)==4 && sizeof(size_t)==8 && sizeof(ssize_t)==8 && sizeof(unsigned long)==8,
               "Original Linux LP64 resource model scalar types"); _Static_assert(sizeof(struct timespec)==16 && _Alignof(struct timespec)==8 && sizeof(sigset_t)==128 && sizeof(struct sigaction)==152 && sizeof(siginfo_t)==128,
               "Original selected signal/time header layouts"); _Static_assert(sizeof(struct qn_version)==72 && _Alignof(struct qn_version)==8 && sizeof(struct qn_slot)==424 && _Alignof(struct qn_slot)==8 && sizeof(struct qn_error)==80 && _Alignof(struct qn_error)==8,
               "Original held native slot/version/error layouts"); _Static_assert(sizeof(struct qn_startup_mode_loan)==800 && _Alignof(struct qn_startup_mode_loan)==8 && sizeof(struct qn_input)==9496 && _Alignof(struct qn_input)==8 && sizeof(struct qn_catalogue)==9360 && _Alignof(struct qn_catalogue)==8,
               "Original enumerated readonly backing journal layouts"); _Static_assert(sizeof(struct qn_gate_write)==352 && _Alignof(struct qn_gate_write)==8 && sizeof(struct qn_terminal_observation)==144 && _Alignof(struct qn_terminal_observation)==8 && sizeof(struct qn_borrow)==176 && _Alignof(struct qn_borrow)==8 && sizeof(struct qn_command)==624 && _Alignof(struct qn_command)==8,
               "Original gate/terminal/borrow/command layouts"); _Static_assert(sizeof(struct qn_absence)==408 && _Alignof(struct qn_absence)==8 && sizeof(struct qn_alias)==8536 && _Alignof(struct qn_alias)==8 && sizeof(struct qn_provision)==9304 && _Alignof(struct qn_provision)==8 && sizeof(struct qn_policy_flag_effect)==168 && _Alignof(struct qn_policy_flag_effect)==8 && sizeof(struct qn_policy_transition)==12736 && _Alignof(struct qn_policy_transition)==8,
               "Original direct PROVISION and policy receipt layouts"); _Static_assert(_Alignof(struct qn_owner)==8 && sizeof(struct qn_owner)== UINT64_C(52856) + UINT64_C(424)*QN_SOURCE_NATIVE_SLOT_COUNT + UINT64_C(9496)*QN_SOURCE_INPUT_COUNT + UINT64_C(624)*QN_SOURCE_COMMAND_COUNT + UINT64_C(9360)*QN_SOURCE_CATALOGUE_COUNT + UINT64_C(408)*QN_SOURCE_ABSENCE_COUNT + UINT64_C(8536)*QN_SOURCE_ALIAS_COUNT,
               "Original source-issued native owner allocation layout"); _Static_assert(sizeof(struct qn_keeper_check)==32 &&
               _Alignof(struct qn_keeper_check)==8 &&
               sizeof(struct qn_keeper_observation_loan)==456 &&
               _Alignof(struct qn_keeper_observation_loan)==8,
               "Original supported private keeper observation layouts");
static struct qn_owner qn;
 static uint64_t qn_clock(void) { struct timespec t; if (clock_gettime(CLOCK_MONOTONIC, &t) < 0 || t.tv_sec < 0 || (uint64_t)t.tv_sec > (UINT64_MAX - (uint64_t)t.tv_nsec) / 1000000000U) return 0; return (uint64_t)t.tv_sec * 1000000000U + (uint64_t)t.tv_nsec; } static int qn_error(const char *operation, int native_errno) { uint64_t ordinal = qn.errors_used++; if (ordinal < QN_ERRORS) { struct qn_error *e = &qn.errors[ordinal]; snprintf(e->operation, sizeof(e->operation), "%s", operation); e->native_errno = native_errno; e->ordinal = ordinal; } if (!qn.first_error) qn.first_error = native_errno ? native_errno : EPROTO; qn.stage = QN_HELD; return -1; } static int qn_owner_check(int permit_held) { uint64_t now; if (qn.pid != getpid() || qn.tid != (pid_t)syscall(SYS_gettid)) return -1; /* Foreign process must not mutate or close this owner's slots. */ now = qn_clock(); if (!now || now < qn.origin_ns || now >= qn.cutoff_ns) return qn_error("original-deadline", ETIMEDOUT); if (!permit_held && (qn.stage == QN_HELD || qn.stage == QN_CLOSED)) return -1; return 0; } static int qn_policy_cleanup_operation(const char *operation) { static const char *const fixed[]={
    "held-handle-recheck","held-path-recheck","FS_IOC_GETFLAGS",
    "source-seal-handle-after","source-seal-path-after","lseek","read",
    "policy-original-immutable-restore","policy-owned-flag-handle",
    "policy-owned-flag-path","policy-partial-flag-handle",
    "policy-partial-flag-path","policy-partial-flag-handle-after",
    "policy-partial-flag-path-after"}; unsigned i; if(!operation) return 0; for(i=0;i<sizeof(fixed)/sizeof(fixed[0]);i++) if(!strcmp(operation,fixed[i])) return 1; return 0; } static int qn_attempt(const char *operation, int metadata) {
  /* Only the Source-selected local failed-prefix getter/read/restore branch.
   * No open, fork, command, dispatch, gate, clock reset or allowance reset.
   * qn_owner_check(1) preserves the existing actual deadline and owner. */ if(qn.controller_policy.partial_cleanup_active) { if(qn.stage!=QN_HELD || !qn.controller_policy.partial_cleanup_attempted || !qn_policy_cleanup_operation(operation) || qn_owner_check(1)<0) return -1; } else if(qn_owner_check(0)<0) return -1; if (!qn.calls_remaining || (metadata && !qn.metadata_remaining)) return qn_error("native-prefix-allocation-exhausted", ENOSPC); --qn.calls_remaining; ++qn.syscall_calls; if (metadata) { --qn.metadata_remaining; ++qn.metadata_calls; } (void)operation; return 0; } static struct qn_version qn_stat_version(const struct stat *s) { struct qn_version v; v.dev=s->st_dev; v.ino=s->st_ino; v.mode=s->st_mode; v.links=s->st_nlink; v.size=s->st_size; v.mtime=s->st_mtim; v.ctime=s->st_ctim; return v; } static int qn_identity_equal(const struct qn_version *a, const struct qn_version *b) { return a->dev==b->dev && a->ino==b->ino && (a->mode&S_IFMT)==(b->mode&S_IFMT); } static int qn_version_equal(const struct qn_version *a, const struct qn_version *b) { return qn_identity_equal(a,b) && a->mode==b->mode && a->links==b->links && a->size==b->size && a->mtime.tv_sec==b->mtime.tv_sec && a->mtime.tv_nsec==b->mtime.tv_nsec && a->ctime.tv_sec==b->ctime.tv_sec && a->ctime.tv_nsec==b->ctime.tv_nsec; } static int qn_component(const char *name) { size_t n = name ? strlen(name) : 0; return n && n<=NAME_MAX && strcmp(name,".") && strcmp(name,"..") && !strchr(name,'/') && !strchr(name,'\n') && !strchr(name,'\r'); } static int qn_decimal(const char *text, uint64_t maximum, uint64_t *value) { uint64_t result=0; const unsigned char *p=(const unsigned char *)text; if (!p || !*p || (p[0]=='0' && p[1])) return -1; while (*p) { if (*p<'0' || *p>'9' || result>(maximum-(uint64_t)(*p-'0'))/10U) return -1; result=result*10U+(uint64_t)(*p++-'0'); } *value=result; return 0; } static int qn_expected_version(const char *text,struct qn_version *v) { uint64_t fields[7]; char part[32]; const char *p=text; unsigned i; if(!p) return -1;
  for(i=0;i<7;i++) { const char *end=strchr(p,','); size_t n; if((i<6&&!end) || (i==6&&end)) return -1; if(!end) end=p+strlen(p); n=(size_t)(end-p); if(!n || n>=sizeof(part)) return -1; memcpy(part,p,n); part[n]=0; if(qn_decimal(part,INT64_MAX,&fields[i])<0) return -1; p=i<6?end+1:end; } if(fields[2]>(uint64_t)UINT_MAX || !fields[3] || (uint64_t)(dev_t)fields[0]!=fields[0] || (uint64_t)(ino_t)fields[1]!=fields[1] || (uint64_t)(off_t)fields[4]!=fields[4]) return -1; v->dev=(dev_t)fields[0]; v->ino=(ino_t)fields[1]; v->mode=(mode_t)fields[2]; v->links=(nlink_t)fields[3]; v->size=(off_t)fields[4]; v->mtime.tv_sec=(time_t)(fields[5]/1000000000U); v->mtime.tv_nsec=(long)(fields[5]%1000000000U); v->ctime.tv_sec=(time_t)(fields[6]/1000000000U); v->ctime.tv_nsec=(long)(fields[6]%1000000000U); return (uint64_t)v->mtime.tv_sec==fields[5]/1000000000U && (uint64_t)v->ctime.tv_sec==fields[6]/1000000000U ? 0:-1; } static int qn_slot_register(int parent, const char *component) { struct qn_slot *s; if (qn.slots_used>=QN_SLOTS || (component && !qn_component(component))) return qn_error("registered-slot-allocation", ENOSPC); s=&qn.slots[qn.slots_used]; memset(s,0,sizeof(*s)); s->registered=1; s->fd=-1; s->parent=parent; if (component) snprintf(s->component,sizeof(s->component),"%s",component); return (int)qn.slots_used++; } static int qn_fstat(int fd, struct stat *s, const char *operation) { if (qn_attempt(operation,1)<0) return -1; if (fstat(fd,s)<0) return qn_error(operation,errno); return 0; } static int qn_fstatat(int parent, const char *component, struct stat *s, const char *operation) { if (parent<0 || (unsigned)parent>=qn.slots_used || qn.slots[parent].fd<0 || !qn_component(component)) return qn_error("unregistered-parent", EINVAL); if (qn_attempt(operation,1)<0) return -1; if (fstatat(qn.slots[parent].fd,component,s,AT_SYMLINK_NOFOLLOW)<0) return qn_error(operation,errno); return 0; } static int qn_check_slot(int number,int stable_version); static int qn_close_slot(int number) { struct qn_slot *s; int result, saved;
  if (qn.pid!=getpid() || qn.tid!=(pid_t)syscall(SYS_gettid) || number<0 || (unsigned)number>=qn.slots_used) return -1; s=&qn.slots[number]; if (s->close_attempted) return qn_error("duplicate-native-close", EALREADY); s->close_attempted=1; if (s->fd<0) { s->close_result=0; return 0; }
  /* Close debt is pre-funded. It remains permitted after the original deadline
   * or a body error; lack of allocation is retained with the close outcome.
   */ if (!qn.calls_remaining) qn_error("close-prefix-allocation-exhausted",ENOSPC); else { --qn.calls_remaining; ++qn.syscall_calls; } errno=0; result=close(s->fd); saved=errno; s->fd=-1; s->close_result=result; s->close_errno=result<0?saved:0;
  /* A failed close is never retried using a potentially recycled number. */ if (result<0) return qn_error("native-close",saved); return 0; } static int qn_open_component(int parent, const char *name, int directory, int ordinary_single_link) { struct stat before, after, handle; struct qn_slot *s; int number=qn_slot_register(parent,name), flags; if (number<0) return -1; s=&qn.slots[number]; if (qn_fstatat(parent,name,&before,"path-before-open")<0) return -1; if ((directory && !S_ISDIR(before.st_mode)) || (!directory && (!S_ISREG(before.st_mode) || (ordinary_single_link && before.st_nlink!=1)))) return qn_error("ordinary-operand-kind-or-link",EINVAL); s->path_before=qn_stat_version(&before); flags=O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK|(directory?O_DIRECTORY:0); if (qn_attempt("openat",0)<0) return -1; s->fd=openat(qn.slots[parent].fd,name,flags); if (s->fd<0) return qn_error("openat",errno); if (qn_fstat(s->fd,&handle,"handle-after-open")<0 || qn_fstatat(parent,name,&after,"path-after-open")<0) return -1; s->handle_before=qn_stat_version(&handle); { struct qn_version observed=qn_stat_version(&after); if (!qn_version_equal(&s->path_before,&observed) || !qn_identity_equal(&s->path_before,&s->handle_before) || (handle.st_mode!=before.st_mode) || handle.st_nlink!=before.st_nlink || (!directory && (handle.st_size!=before.st_size || handle.st_mtim.tv_sec!=before.st_mtim.tv_sec || handle.st_mtim.tv_nsec!=before.st_mtim.tv_nsec))) return qn_error("path-handle-open-disagreement",ESTALE); } return number; } static int qn_existing_directory(int parent,const char *name) { unsigned i; for(i=0;i<qn.slots_used;i++) { struct qn_slot *s=&qn.slots[i]; if(s->parent==parent && s->fd>=0 && !s->close_attempted && !strcmp(s->component,name) && S_ISDIR(s->handle_before.mode)) return qn_check_slot((int)i,0)<0?-1:(int)i; } return qn_open_component(parent,name,1,0); } static int qn_check_slot(int number, int stable_version) { struct qn_slot *s; struct stat handle,path; struct qn_version hv,pv;
  if (number<0 || (unsigned)number>=qn.slots_used || qn.slots[number].fd<0) return qn_error("native-slot-not-live",EBADF); s=&qn.slots[number]; if (qn_fstat(s->fd,&handle,"held-handle-recheck")<0) return -1; hv=qn_stat_version(&handle); if (!qn_identity_equal(&hv,&s->handle_before) || (stable_version && !qn_version_equal(&hv,&s->handle_before))) return qn_error("held-handle-generation-changed",ESTALE); if (s->parent>=0) { if (qn_fstatat(s->parent,s->component,&path,"held-path-recheck")<0) return -1; pv=qn_stat_version(&path); if (!qn_identity_equal(&pv,&hv) || (stable_version && !qn_version_equal(&pv,&s->path_before))) return qn_error("held-path-generation-changed",ESTALE); } return 0; } static int qn_check_held_parent(int number) { struct stat st; struct qn_version current; if(number<0 || (unsigned)number>=qn.slots_used || qn.slots[number].fd<0 || qn_fstat(qn.slots[number].fd,&st,"held-parent-handle-generation")<0) return -1; current=qn_stat_version(&st); return S_ISDIR(current.mode) && qn_identity_equal(&current,&qn.slots[number].handle_before) ? 0: qn_error("held-parent-handle-substitution",ESTALE); } static ssize_t qn_read(int slot, void *buffer, size_t request) { ssize_t n; if (!request || request>QN_CHUNK || request>qn.read_remaining || slot<0 || (unsigned)slot>=qn.slots_used || qn.slots[slot].fd<0) return qn_error("bounded-read-admission",ENOSPC); if (qn_attempt("read",0)<0) return -1; if (request>qn.largest_read) qn.largest_read=request; n=read(qn.slots[slot].fd,buffer,request); if (n<0) return qn_error("native-read",errno); qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; return n; } static int qn_seek_start(int slot) { if (qn_attempt("lseek",0)<0) return -1; if (lseek(qn.slots[slot].fd,0,SEEK_SET)!=0) return qn_error("native-seek",errno?errno:EIO); return 0; } static int qn_read_text(int slot, char *out, size_t capacity, size_t *length) { struct stat before,after,path; struct qn_version b,a,p; size_t used=0; ssize_t n; unsigned char extra;
  if (!capacity || capacity>QN_DATA || qn_check_slot(slot,0)<0 || qn_fstat(qn.slots[slot].fd,&before,"read-handle-before")<0 || qn_seek_start(slot)<0) return -1; b=qn_stat_version(&before); while (used<capacity-1) { size_t wanted=capacity-1-used; if (wanted>QN_CHUNK) wanted=QN_CHUNK; n=qn_read(slot,out+used,wanted); if (n<0) return -1; if (!n) break; if (memchr(out+used,0,(size_t)n)) return qn_error("control-text-NUL",EPROTO); used+=(size_t)n; } if (used==capacity-1) { n=qn_read(slot,&extra,1); if (n<0) return -1; if (n) return qn_error("native-control-extent",EFBIG); } if (qn_fstat(qn.slots[slot].fd,&after,"read-handle-after")<0 || qn_fstatat(qn.slots[slot].parent,qn.slots[slot].component,&path,
                  "read-path-after")<0) return -1; a=qn_stat_version(&after); p=qn_stat_version(&path); if (!qn_version_equal(&b,&a) || !qn_identity_equal(&a,&p)) return qn_error("native-control-read-generation",ESTALE); out[used]=0; *length=used; return 0; } static int qn_read_component_text(int parent,const char *name,char *out, size_t cap,size_t *length) { int number=qn_open_component(parent,name,0,0), result; if (number<0) return -1; result=qn_read_text(number,out,cap,length); if (qn_close_slot(number)<0) result=-1; return result; } static int qn_parse_limit(const char *text, uint64_t *result) { char value[64]; size_t n=strlen(text); if (!n || n>=sizeof(value) || text[n-1]!='\n') return -1; memcpy(value,text,n-1); value[n-1]=0; if (!strcmp(value,"max")) { *result=UINT64_MAX; return 0; } return qn_decimal(value,UINT64_MAX,result); } static int qn_cpu_limit(const char *text,uint64_t *quota,uint64_t *period) { char left[64],right[64]; const char *space=strchr(text,' '); size_t n; if (!space || strchr(space+1,' ') || !(n=(size_t)(space-text)) || n>=sizeof(left)) return -1; memcpy(left,text,n); left[n]=0; n=strlen(space+1); if (!n || n>=sizeof(right) || space[1+n-1]!='\n') return -1; memcpy(right,space+1,n-1); right[n-1]=0; if (!strcmp(left,"max")) *quota=UINT64_MAX; else if (qn_decimal(left,UINT64_MAX,quota)<0) return -1; return qn_decimal(right,UINT64_MAX,period)<0 || !*period ? -1 : 0; } static int qn_kernel_limits(int directory, int exact_common, uint64_t *memory,uint64_t *tasks, uint64_t *quota,uint64_t *period) { char value[256]; size_t n; uint64_t swap; if (qn_read_component_text(directory,"memory.max",value,sizeof(value),&n)<0 || qn_parse_limit(value,memory)<0 || qn_read_component_text(directory,"memory.swap.max",value,sizeof(value),&n)<0 || qn_parse_limit(value,&swap)<0 || qn_read_component_text(directory,"pids.max",value,sizeof(value),&n)<0 || qn_parse_limit(value,tasks)<0 || qn_read_component_text(directory,"cpu.max",value,sizeof(value),&n)<0 || qn_cpu_limit(value,quota,period)<0)
    return qn_error("native-kernel-limit-shape",EPROTO); if (exact_common && (*memory!=QN_WHOLE_MEMORY || swap!=0 || *tasks!=QN_WHOLE_TASKS || *quota!=QN_CPU_QUOTA || *period!=QN_CPU_PERIOD)) return qn_error("native-common-limit-readback",EPROTO); return 0; } static int qn_safe_root(const char *path) { int slot, next; const char *p=path; char component[NAME_MAX+1]; size_t n; struct stat st; if (!path || path[0]!='/' || path[1]=='/' || strlen(path)>=QN_PATH) return qn_error("absolute-native-root",EINVAL); slot=0; if (!qn.slots_used) { slot=qn_slot_register(-1,0); if (slot<0 || qn_attempt("open-root",0)<0) return -1; qn.slots[slot].fd=open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC); if (qn.slots[slot].fd<0) return qn_error("open-root",errno); if (qn_fstat(qn.slots[slot].fd,&st,"root-handle")<0 || !S_ISDIR(st.st_mode)) return qn_error("root-not-directory",EINVAL); qn.slots[slot].handle_before=qn.slots[slot].path_before=qn_stat_version(&st); } else if (qn.slots[slot].fd<0 || qn_check_slot(slot,0)<0) return -1; ++p; while (*p) { const char *end=strchr(p,'/'); if (!end) end=p+strlen(p); n=(size_t)(end-p); if (!n || n>NAME_MAX) return qn_error("native-root-component",EINVAL); memcpy(component,p,n); component[n]=0; next=qn_existing_directory(slot,component); if (next<0) return -1; slot=next; p=*end?end+1:end; if (!*p && *end) return qn_error("native-root-trailing-slash",EINVAL); } return slot; } static int qn_regular_absolute(const char *path) { char parent[QN_PATH], name[NAME_MAX+1]; const char *slash; int directory; size_t n; if (!path || path[0]!='/' || !(slash=strrchr(path,'/')) || !slash[1] || strlen(path)>=QN_PATH || !qn_component(slash+1)) return qn_error("ordinary-input-absolute-path",EINVAL); n=(size_t)(slash-path); if (!n) n=1; memcpy(parent,path,n); parent[n]=0; snprintf(name,sizeof(name),"%s",slash+1); directory=qn_safe_root(parent); if (directory<0) return -1; return qn_open_component(directory,name,0,1); } static int qn_immutable_slot(int slot,unsigned long *flags) { int current=0;
  if (qn_attempt("FS_IOC_GETFLAGS",0)<0) return -1; if (ioctl(qn.slots[slot].fd,FS_IOC_GETFLAGS,&current)<0) return qn_error("native-startup-protection-unavailable",errno); if (!(current&FS_IMMUTABLE_FL)) return qn_error("native-startup-inode-not-immutable",EPERM); *flags=(unsigned long)current; return 0; } static int qn_current_flags(int slot,unsigned long *flags) { int current=0; if(qn_attempt("FS_IOC_GETFLAGS",0)<0) return -1; if(ioctl(qn.slots[slot].fd,FS_IOC_GETFLAGS,&current)<0) return qn_error("native-startup-flag-getter",errno); *flags=(unsigned long)current; return 0; } static int qn_compare_slots(int actual,int expected,uint64_t extent) { unsigned char left[QN_CHUNK],right[QN_CHUNK],extra; uint64_t remaining=extent; ssize_t n,m; size_t have; struct stat before_l,before_r,after_l,after_r; struct qn_version bl,br,al,ar; if (qn_check_slot(actual,1)<0 || qn_check_slot(expected,1)<0 || qn_fstat(qn.slots[actual].fd,&before_l,"compare-original-before")<0 || qn_fstat(qn.slots[expected].fd,&before_r,"compare-baseline-before")<0 || qn_seek_start(actual)<0 || qn_seek_start(expected)<0) return -1; bl=qn_stat_version(&before_l); br=qn_stat_version(&before_r); if (before_l.st_size<0 || before_r.st_size<0 || (uint64_t)before_l.st_size!=extent || (uint64_t)before_r.st_size!=extent || qn_identity_equal(&bl,&br)) return qn_error("startup-independent-extent",EPROTO); while (remaining) { size_t request=remaining>QN_CHUNK?QN_CHUNK:(size_t)remaining; n=qn_read(actual,left,request); if (n<0) return -1; if (!n) return qn_error("startup-original-short-read",EIO); have=0; while (have<(size_t)n) { m=qn_read(expected,right+have,(size_t)n-have); if (m<0) return -1; if (!m) return qn_error("startup-baseline-short-read",EIO); have+=(size_t)m; } if (memcmp(left,right,(size_t)n)) return qn_error("startup-original-bytes",ESTALE); remaining-=(uint64_t)n; } n=qn_read(actual,&extra,1); if (n<0) return -1; if (n) return qn_error("startup-original-suffix",EFBIG); n=qn_read(expected,&extra,1); if (n<0) return -1;
  if (n) return qn_error("startup-baseline-suffix",EFBIG); if (qn_fstat(qn.slots[actual].fd,&after_l,"compare-original-after")<0 || qn_fstat(qn.slots[expected].fd,&after_r,"compare-baseline-after")<0) return -1; al=qn_stat_version(&after_l); ar=qn_stat_version(&after_r); if (!qn_version_equal(&bl,&al) || !qn_version_equal(&br,&ar) || qn_check_slot(actual,1)<0 || qn_check_slot(expected,1)<0) return qn_error("startup-generation-after-read",ESTALE); return 0; } static int qn_startup_check(void) { unsigned i; unsigned long flags; if (qn_owner_check(0)<0 || !qn.catalogue_complete) return -1; for (i=0;i<qn.input_count;i++) { struct qn_input *p=&qn.inputs[i]; int left=-1,right=-1,result=0; left=qn_regular_absolute(p->source); right=qn_regular_absolute(p->snapshot); if(left<0 || right<0) result=-1; if(result==0 && (!qn_version_equal(&p->protected_source_path,&qn.slots[left].path_before) || !qn_version_equal(&p->protected_source_handle,&qn.slots[left].handle_before) || !qn_version_equal(&p->protected_baseline_path,&qn.slots[right].path_before) || !qn_version_equal(&p->protected_baseline_handle,&qn.slots[right].handle_before))) result=qn_error("startup-protected-generation-open",ESTALE); if (result==0 && (!p->occupied || qn_immutable_slot(left,&flags)<0 || flags!=p->flags || qn_immutable_slot(right,&flags)<0 || flags!=p->baseline_flags || qn_compare_slots(left,right,p->length)<0)) result=qn_error("startup-protected-input-check",ESTALE); if(right>=0 && qn_close_slot(right)<0) result=-1; if(left>=0 && qn_close_slot(left)<0) result=-1; if(result<0) return -1; } return 0; } static int qn_catalogue_check(struct qn_catalogue *c) { unsigned char entries[QN_CHUNK]; unsigned char *seen=0; size_t found=0; struct qn_linux_dirent64 { uint64_t ino; int64_t offset; unsigned short reclen; unsigned char type; char name[]; }; ssize_t n; unsigned long flags; int result=-1; if(qn_check_slot(c->directory_slot,1)<0 || qn_check_slot(c->baseline_slot,1)<0 || qn_immutable_slot(c->directory_slot,&flags)<0 || flags!=c->flags ||
      qn_immutable_slot(c->baseline_slot,&flags)<0 || flags!=c->baseline_flags || qn_seek_start(c->directory_slot)<0) return -1; seen=calloc(c->name_count?c->name_count:1,1); if(!seen) return qn_error("startup-directory-comparison-storage",ENOMEM); for(;;) { size_t at=0; if(qn_attempt("startup-directory-getdents64",0)<0 || QN_CHUNK>qn.read_remaining) goto done; n=syscall(SYS_getdents64,qn.slots[c->directory_slot].fd,entries,QN_CHUNK); if(n<0) { qn_error("startup-directory-getdents64",errno); goto done; } qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; if(qn.largest_read<QN_CHUNK) qn.largest_read=QN_CHUNK; if(!n) break; while(at<(size_t)n) { struct qn_linux_dirent64 *entry=(struct qn_linux_dirent64 *)(entries+at); const char *expected=c->names; size_t ordinal=0,len; if((size_t)n-at<offsetof(struct qn_linux_dirent64,name)+1 || entry->reclen<offsetof(struct qn_linux_dirent64,name)+1 || entry->reclen>(size_t)n-at || !memchr(entry->name,0,entry->reclen - offsetof(struct qn_linux_dirent64,name))) { qn_error("startup-directory-native-shape",EPROTO); goto done; } len=strlen(entry->name); at+=entry->reclen; if(!strcmp(entry->name,".") || !strcmp(entry->name,"..")) continue; if(!qn_component(entry->name)) { qn_error("startup-directory-spelling",EPROTO); goto done; } while(*expected) { const char *end=strchr(expected,'\n'); if(!end) { qn_error("startup-directory-baseline-shape",EPROTO); goto done; } if((size_t)(end-expected)==len && !memcmp(expected,entry->name,len)) break; expected=end+1; ++ordinal; } if(!*expected || ordinal>=c->name_count || seen[ordinal]) { qn_error("startup-directory-membership",ESTALE); goto done; } seen[ordinal]=1; ++found; } } if(found!=c->name_count || qn_check_slot(c->directory_slot,1)<0 || qn_check_slot(c->baseline_slot,1)<0) { qn_error("startup-directory-complete-membership",ESTALE); goto done; } result=0; done: free(seen); return result; } static int qn_absence_check(struct qn_absence *a) { struct stat st;
  if(qn_check_slot(a->parent_slot,1)<0 || qn_attempt("startup-absence-fstatat",1)<0) return -1; errno=0; if(fstatat(qn.slots[a->parent_slot].fd,a->component,&st,AT_SYMLINK_NOFOLLOW)==0 || errno!=ENOENT) return qn_error("startup-absence-not-proven",errno?errno:EEXIST); return 0; } static int qn_complete_startup_check(void) { unsigned i; if(qn_startup_check()<0 || !qn.catalogue_complete) return -1; for(i=0;i<qn.catalogue_count;i++) if(qn_catalogue_check(&qn.catalogues[i])<0) return -1; for(i=0;i<qn.absence_count;i++) if(qn_absence_check(&qn.absences[i])<0) return -1; return 0; } static int qn_hex32(const char *text) { unsigned i; if (!text || strlen(text)!=32) return 0; for(i=0;i<32;i++) if (!((text[i]>='0'&&text[i]<='9') || (text[i]>='a'&&text[i]<='f'))) return 0; return 1; } static int qn_bind_private(const char *name,uint64_t value) { char decimal[32]; SHELL_VAR *v;
  /* This binding is process-local diagnostic data; it is not exported, a
   * wire permission or a substitute for the corresponding held native state.
   */ v=find_variable_noref(name); if (v && (readonly_p(v) || exported_p(v) || nameref_p(v) || array_p(v) || assoc_p(v) || v->dynamic_value || v->assign_func)) return qn_error("private-shell-data-binding",EINVAL); snprintf(decimal,sizeof(decimal),"%" PRIu64,value); v=bind_variable(name,decimal,0); if (!v || exported_p(v) || readonly_p(v) || strcmp(value_cell(v),decimal)) return qn_error("private-shell-data-readback",EPROTO); return 0; } static int qn_publish_counters(void) { if(qn_bind_private("_qtt_native_origin_ns",qn.origin_ns)<0 || qn_bind_private("_qtt_native_calls_used",qn.syscall_calls)<0 || qn_bind_private("_qtt_native_reads_used",qn.read_bytes)<0 || qn_bind_private("_qtt_native_metadata_used",qn.metadata_calls)<0 || qn_bind_private("_qtt_native_largest_read",qn.largest_read)<0) return -1; if(qn.provision.observed && qn.provision.receipt_decoded) return qn_bind_private("_qtt_native_parent_pid",(uint64_t)qn.provision.receipt_parent_pid); return 0; } static int qn_capture_startup(void); static int qn_provision_prepare(void); static int qn_provision_bind(void); static int qn_provision_release_observe(void); static int qn_provision_return(int terminal_status);
/* This post-load join checks the SAME previously acquired job enclosure.
 * Its current kernel observations do not certify earlier compiler/loader
 * protection. The original before-build supplier remains independently bound.
 */ static int qn_holder_ancestor(void) { char decimal[32],text[256],absolute[QN_PATH],expected[96]; size_t n,length; int process=-1,record=-1,result=-1,at; uint64_t memory,tasks,quota,period; const char *last; char *cut; snprintf(decimal,sizeof(decimal),"%ld",(long)qn.pid); process=qn_open_component(qn.proc_slot,decimal,1,0); if(process<0) return -1; record=qn_open_component(process,"cgroup",0,0); if(record<0 || qn_read_text(record,text,sizeof(text),&n)<0) goto done; if(n<7 || strncmp(text,"0::/",4) || text[n-1]!='\n' || memchr(text,'\n',n-1) || strstr(text,"//") || strstr(text,"/../") || strstr(text,"/./") || strchr(text,'\\')) { qn_error("original-holder-cgroup-shape",EPROTO); goto done; } text[n-1]=0; cut=strrchr(text+3,'/'); snprintf(expected,sizeof(expected),"%scontroller.service",qn.stem); if(!cut || cut==text+3 || strcmp(cut+1,expected)) { qn_error("original-holder-selected-service-membership",ESTALE); goto done; } *cut=0; length=strlen(text+3); if(length>=sizeof(qn.ancestor_group)) { qn_error("original-holder-ancestor-locator-extent",ENAMETOOLONG); goto done; } snprintf(qn.ancestor_group,sizeof(qn.ancestor_group),"%s",text+3); last=strrchr(qn.ancestor_group,'/'); if(!last || !last[1]) { qn_error("original-holder-ancestor-name",EPROTO); goto done; } ++last; length=strlen(last); if(length<=6 || strcmp(last+length-6,".slice")) { qn_error("original-holder-native-slice-required",EPROTO); goto done; } for(n=0;n<length-6;n++) if(!((last[n]>='a'&&last[n]<='z') || (last[n]>='A'&&last[n]<='Z') || (last[n]>='0'&&last[n]<='9') || last[n]=='_' || last[n]=='-')) { qn_error("original-holder-native-slice-spelling",EPROTO); goto done; } if(snprintf(qn.common,sizeof(qn.common),"%.*s-%s.slice",(int)(length-6),last,qn.stem) >=(int)sizeof(qn.common)) { qn_error("source-unit-locator-extent",ENAMETOOLONG); goto done; } if(snprintf(absolute,sizeof(absolute),"%s%s",QN_CGROUP_ROOT,qn.ancestor_group) >=(int)sizeof(absolute)) { qn_error("original-holder-absolute-ancestor-extent",ENAMETOOLONG); goto done; }
  qn.ancestor_slot=qn_safe_root(absolute); if(qn.ancestor_slot<0 || qn.ancestor_slot==qn.root_slot) goto done; at=qn.ancestor_slot; while(at!=qn.root_slot) { if(at<0 || (unsigned)at>=qn.slots_used || qn_check_slot(at,0)<0 || qn_kernel_limits(at,at==qn.ancestor_slot,&memory,&tasks,&quota,&period)<0) goto done; if(memory<QN_WHOLE_MEMORY || tasks<QN_WHOLE_TASKS || (quota!=UINT64_MAX && (period>UINT64_MAX/2 || quota<2*period))) { qn_error("original-holder-real-ancestor-intersection",ENOSPC); goto done; } at=qn.slots[at].parent; } if(qn_check_slot(qn.root_slot,0)<0) goto done; result=0; done: if(record>=0 && !qn.slots[record].close_attempted && qn_close_slot(record)<0) result=-1; if(process>=0 && !qn.slots[process].close_attempted && qn_close_slot(process)<0) result=-1; return result; } static int qn_init(const char *run,const char *attempt,const char *phase, const char *original_origin,const char *calls,const char *reads,const char *metadata) { uint64_t a,b,p,c,r,m,origin,now; struct statfs fs; SHELL_VAR *version; if (qn.entry_attempted) return -1; version=find_variable_noref("BASH_VERSION"); if(!version || version->dynamic_value || version->assign_func || !version->value || strcmp(version->value,QN_SOURCE_BASH_VERSION) || strncmp(version->value,"5.2.",4)) return -1; now=qn_clock(); if (qn_decimal(original_origin,UINT64_MAX-QN_DURATION,&origin)<0 || !origin || !now || origin>now || now>=origin+QN_DURATION || qn_decimal(run,UINT64_C(9999999999999999999),&a)<0 || !a || qn_decimal(attempt,UINT64_C(9999999999999999999),&b)<0 || !b || qn_decimal(phase,13,&p)<0 || !p || qn_decimal(calls,UINT64_MAX,&c)<0 || c!=QN_SOURCE_CALLS || !c || qn_decimal(reads,UINT64_MAX,&r)<0 || r!=QN_SOURCE_READ_BYTES || !r || qn_decimal(metadata,UINT64_MAX,&m)<0 || m!=QN_SOURCE_METADATA_CALLS || !m || m>c) return -1; qn.entry_attempted=1; qn.pid=getpid(); qn.tid=(pid_t)syscall(SYS_gettid); qn.origin_ns=origin; qn.cutoff_ns=origin+QN_DURATION; qn.calls_remaining=c; qn.read_remaining=r; qn.metadata_remaining=m;
  if(QN_SOURCE_RETAINED_HEAP_BYTES>QN_WHOLE_MEMORY || sizeof(qn)>QN_SOURCE_RETAINED_HEAP_BYTES) return qn_error("native-static-storage-exceeds-original-allocation",ENOSPC); qn.heap_remaining=QN_SOURCE_RETAINED_HEAP_BYTES-sizeof(qn); qn.realloc_peak_remaining=QN_SOURCE_REALLOC_ATTEMPT_BYTES; qn.write_remaining=QN_SOURCE_WRITE_BYTES; qn.snapshot_root_slot=-1; { static const char *const phases[]={"fast-preflight","deterministic-validators-a",
      "deterministic-validators-b","deterministic-validators-c","pytest-shard-1",
      "pytest-shard-2","pytest-shard-3","pytest-shard-4","pytest-shard-5",
      "pytest-shard-6","pytest-shard-7","pytest-shard-8","post-validation"}; snprintf(qn.phase,sizeof(qn.phase),"%s",phases[p-1]); } qn.stage=QN_PREPARING; qn.root_slot=qn.ancestor_slot=qn.common_slot=qn.bootstrap_slot=qn.proc_slot=-1; snprintf(qn.stem,sizeof(qn.stem),"qtt%" PRIu64 "n%" PRIu64 "p%" PRIu64,a,b,p); if (strlen(qn.stem)>45) return qn_error("source-unit-locator-extent",EINVAL); snprintf(qn.common,sizeof(qn.common),"%s.slice",qn.stem); snprintf(qn.bootstrap,sizeof(qn.bootstrap),"%sbootstrap.scope",qn.stem); qn.root_slot=qn_safe_root(QN_CGROUP_ROOT); if (qn.root_slot<0 || qn_attempt("fstatfs-cgroup-root",1)<0) return -1; if (fstatfs(qn.slots[qn.root_slot].fd,&fs)<0) return qn_error("native-cgroup-root-fstatfs",errno); if ((unsigned long)fs.f_type!=CGROUP2_SUPER_MAGIC) return qn_error("native-cgroup2-required",ENODEV); qn.proc_slot=qn_safe_root("/proc"); if (qn.proc_slot<0 || qn_attempt("fstatfs-proc-root",1)<0) return -1; if (fstatfs(qn.slots[qn.proc_slot].fd,&fs)<0 || (unsigned long)fs.f_type!=PROC_SUPER_MAGIC) return qn_error("native-procfs-required",errno?errno:ENODEV); if(qn_holder_ancestor()<0 || qn_capture_startup()<0) return -1; return qn_publish_counters(); } static int qn_prebirth(const char *invocation) { uint64_t memory,tasks,quota,period; if (qn.stage!=QN_PREPARING || qn.common_slot>=0 || qn.bootstrap_slot>=0 || !qn_hex32(invocation) || qn_check_slot(qn.root_slot,0)<0) return -1; if(qn.ancestor_slot<0 || qn_check_slot(qn.ancestor_slot,0)<0) return -1; qn.common_slot=qn_open_component(qn.ancestor_slot,qn.common,1,0); if (qn.common_slot<0 || qn_kernel_limits(qn.common_slot,1,&memory,&tasks,&quota,&period)<0) return -1; if (qn.slots[qn.common_slot].parent!=qn.ancestor_slot) return qn_error("native-ancestor-domain",EXDEV); memcpy(qn.invocation,invocation,sizeof(qn.invocation));
  /* The original native preparation forks only a gated direct child, and
   * creates this original scope over that factual PID BEFORE target exec.
   */ if(qn_provision_prepare()<0) return -1; qn.bootstrap_slot=qn_open_component(qn.common_slot,qn.bootstrap,1,0); if(qn.bootstrap_slot<0 || qn.slots[qn.bootstrap_slot].parent!=qn.common_slot || qn_kernel_limits(qn.bootstrap_slot,0,&memory,&tasks,&quota,&period)<0) return -1; if(memory<QN_WHOLE_MEMORY || tasks<QN_WHOLE_TASKS || (quota!=UINT64_MAX && (period>UINT64_MAX/2 || quota<2*period))) return qn_error("native-bootstrap-original-limit-intersection",ENOSPC); if(qn_check_slot(qn.ancestor_slot,0)<0 || qn_check_slot(qn.common_slot,0)<0 || qn_check_slot(qn.bootstrap_slot,0)<0) return -1; qn.stage=QN_PREBIRTH; return qn_publish_counters(); } static int qn_hold_bootstrap_if_present(void) { struct stat st; int slot; if(qn.bootstrap_slot>=0) return qn_check_held_parent(qn.bootstrap_slot); if(qn_check_slot(qn.common_slot,0)<0 || qn_attempt("original-bootstrap-first-path",1)<0) return -1; errno=0; if(fstatat(qn.slots[qn.common_slot].fd,qn.bootstrap,&st,AT_SYMLINK_NOFOLLOW)<0) { if(errno==ENOENT) return 0; return qn_error("original-bootstrap-first-path",errno); } if(!S_ISDIR(st.st_mode)) return qn_error("original-bootstrap-kind",EINVAL); slot=qn_open_component(qn.common_slot,qn.bootstrap,1,0); if(slot<0) return -1; qn.bootstrap_slot=slot; return 0; } static int qn_proc_start(pid_t pid,uint64_t *start) { char decimal[32],text[4096]; size_t n; int directory,stat_slot,result=-1; char *close,*p,*end; unsigned field; snprintf(decimal,sizeof(decimal),"%ld",(long)pid); directory=qn_open_component(qn.proc_slot,decimal,1,0); if(directory<0) return -1; stat_slot=qn_open_component(directory,"stat",0,0); if(stat_slot<0) goto done; if(qn_read_text(stat_slot,text,sizeof(text),&n)<0) goto done; close=strrchr(text,')'); if(!close || close[1]!=' ' || !close[2] || close[3]!=' ') { qn_error("native-process-stat-shape",EPROTO); goto done; } p=close+4; for(field=4;field<22;field++) { end=strchr(p,' '); if(!end || end==p) { qn_error("native-process-stat-field",EPROTO); goto done; } p=end+1; }
  end=strchr(p,' '); if(!end || end==p || (size_t)(end-p)>=32) { qn_error("native-process-start-field",EPROTO); goto done; } *end=0; if(qn_decimal(p,UINT64_MAX,start)<0) { qn_error("native-process-start-value",EPROTO); goto done; } result=0; done: if(stat_slot>=0 && qn_close_slot(stat_slot)<0) result=-1; if(qn_close_slot(directory)<0) result=-1; return result; } static int qn_pidfd_slot(pid_t pid) { int number=qn_slot_register(-1,0),flags; if(number<0 || qn_attempt("pidfd_open",0)<0) return -1; qn.slots[number].fd=(int)syscall(SYS_pidfd_open,pid,0); if(qn.slots[number].fd<0) return qn_error("native-pidfd-open",errno); if(qn_attempt("pidfd-getfd",0)<0) return -1; flags=fcntl(qn.slots[number].fd,F_GETFD); if(flags<0 || !(flags&FD_CLOEXEC)) return qn_error("native-pidfd-inheritance",errno?errno:EPROTO); return number; }
/* Parent-only gate write, invoked AFTER the original command's fork. The
 * already-forked child keeps its original signal dispositions. Each command
 * owns a distinct one-use record; previous occurrences are never overwritten.
 */ static int qn_gate_write_original(struct qn_command *c,int gate_slot) { struct qn_gate_write *g=&c->gate_write; struct sigaction ignored; unsigned char token=0x51; int result=0; if(g->registered) return qn_error("original-gate-write-single-use",EALREADY); memset(g,0,sizeof(*g)); g->registered=1; if(!c->registered || !c->pending || !c->child_created || gate_slot<0 || (unsigned)gate_slot>=qn.slots_used || qn.slots[gate_slot].fd<0 || qn.slots[gate_slot].close_attempted || qn_owner_check(0)<0) return qn_error("original-gate-write-owner",EPROTO);
  /* Fixed whole-effect/restore tranche: pending getter, atomic install and
   * original-action acquisition, exact one-byte write, exact restoration.
   * Getter convention makes sigpending the one metadata attempt. Reserving
   * four calls BEFORE any signal effect permits restoration even after a
   * write failure enters HELD or the original deadline expires. No refund or
   * qn_attempt reset is performed; actual executed attempts count separately.
   */ if(qn.calls_remaining<4 || qn.metadata_remaining<1) return qn_error("original-gate-write-tranche-exhausted",ENOSPC); g->reserved=1; qn.calls_remaining-=4; --qn.metadata_remaining; g->pending_attempted=1; ++qn.syscall_calls; ++qn.metadata_calls; errno=0; g->pending_result=sigpending(&g->pending); g->pending_errno=g->pending_result<0?errno:0; if(g->pending_result<0) return qn_error("original-gate-write-sigpending",g->pending_errno); g->preexisting_pending=sigismember(&g->pending,SIGPIPE); if(g->preexisting_pending!=0) return qn_error("original-gate-write-preexisting-SIGPIPE", g->preexisting_pending<0?EINVAL:EBUSY); memset(&ignored,0,sizeof(ignored)); ignored.sa_handler=SIG_IGN; if(sigemptyset(&ignored.sa_mask)<0) return qn_error("original-gate-write-empty-mask",errno);
  /* sigaction atomically obtains the actual old action and installs IGN.
   * prior_action is meaningful ONLY after this actual install returns0.
   */ g->install_attempted=1; ++qn.syscall_calls; errno=0; g->install_result=sigaction(SIGPIPE,&ignored,&g->prior_action); g->install_errno=g->install_result<0?errno:0; if(g->install_result<0) return qn_error("original-gate-write-SIGPIPE-install",g->install_errno); g->prior_valid=1; g->write_attempted=1; ++qn.syscall_calls; errno=0; g->write_result=write(qn.slots[gate_slot].fd,&token,1); g->write_errno=g->write_result<0?errno:0; if(g->write_result!=1) { qn_error("original-gate-write-byte",g->write_errno?g->write_errno:EIO); result=-1; }
  /* Every known installed outcome restores the exact retained action. This
   * reserved restoration is allowed while HELD and beyond the body deadline.
   * A failed restore remains HELD with the actual raw outcome and old action.
   */ g->restore_attempted=1; ++qn.syscall_calls; errno=0; g->restore_result=sigaction(SIGPIPE,&g->prior_action,0); g->restore_errno=g->restore_result<0?errno:0; if(g->restore_result<0) { qn_error("original-gate-write-SIGPIPE-restore",g->restore_errno); result=-1; } return result; }
/* One original observation per purpose. Native signal/error/zero-pid data is
 * retained before the caller validates an accepted terminal status. A failed
 * or signalled prefix must not disappear with a local siginfo_t on return.
 */ static int qn_waitid_original(struct qn_terminal_observation *o,int pid_slot, const char *operation) { if(o->registered) return qn_error("original-waitid-observation-single-use",EALREADY); memset(o,0,sizeof(*o)); o->registered=1; if(pid_slot<0 || (unsigned)pid_slot>=qn.slots_used || qn.slots[pid_slot].fd<0 || qn.slots[pid_slot].close_attempted) return qn_error("original-waitid-observation-slot",EINVAL); if(qn_attempt(operation,0)<0) return -1; o->native_attempted=1; errno=0; o->result=waitid(P_PIDFD,(id_t)qn.slots[pid_slot].fd,&o->info, WEXITED|WNOHANG|WNOWAIT); o->native_errno=o->result<0?errno:0; if(o->result<0) return qn_error(operation,o->native_errno); return 0; } static int qn_borrow(enum qn_role role,pid_t pid) { struct qn_borrow *b; uint64_t before,after; if(qn_owner_check(0)<0 || role<0 || role>=QN_BORROWS || pid<=0 || pid==qn.pid || (qn.stage!=QN_PREBIRTH && qn.stage!=QN_RUNNING) || qn_startup_check()<0) return -1; b=&qn.borrows[role]; if(b->registered) return qn_error("native-borrow-single-use",EALREADY); b->registered=1; b->pid=pid; b->pid_slot=-1; if(qn_proc_start(pid,&before)<0) return -1; b->pid_slot=qn_pidfd_slot(pid); if(b->pid_slot<0 || qn_proc_start(pid,&after)<0) return -1; if(before!=after) return qn_error("native-borrow-process-generation",ESTALE); b->start_ticks=before; if(role==QN_PROVISION) { qn.scope_started=1; qn.stage=QN_RUNNING; } return qn_publish_counters(); } static int qn_return(enum qn_role role,int terminal_status) { struct qn_borrow *b; struct pollfd p; struct qn_terminal_observation *observed; int ready; if(role==QN_PROVISION && qn.provision.attempted) return qn_provision_return(terminal_status); if(qn_owner_check(0)<0 || role<0 || role>=QN_BORROWS) return -1; b=&qn.borrows[role]; if(!b->registered || b->returned || b->pid_slot<0) return qn_error("native-borrow-return-state",EINVAL); p.fd=qn.slots[b->pid_slot].fd; p.events=POLLIN; p.revents=0; if(qn_attempt("pidfd-terminal-poll",0)<0) return -1; ready=poll(&p,1,0);
  if(ready!=1 || !(p.revents&POLLIN) || (p.revents&(POLLNVAL|POLLERR))) return qn_error("native-borrow-terminal-unproven",errno?errno:EBUSY);
  /* ECHILD is not evidence that a descendant's exit status is known. This
   * original Bash owner can return only its own still-waitable direct child.
   * Raw native error/signal/zero-pid observations remain in this borrow.
   */ observed=&b->return_observation; if(qn_waitid_original(observed,b->pid_slot,"pidfd-waitid-WNOWAIT")<0) return -1; if(observed->info.si_pid!=b->pid || observed->info.si_code!=CLD_EXITED || observed->info.si_status!=terminal_status) return qn_error("native-borrow-terminal-status",EPROTO); b->terminal_code=observed->info.si_code; b->terminal_status=observed->info.si_status; if(qn_startup_check()<0 || qn_close_slot(b->pid_slot)<0) return -1; b->returned=1; if(role==QN_PROVISION) qn.stage=QN_TERMINAL; return qn_publish_counters(); } static int qn_empty_directory(int parent,const char *name,int persistent, int must_be_absent) { struct stat current; int slot=-1,result=-1; char text[256]; size_t n; if((must_be_absent?qn_check_held_parent(parent):qn_check_slot(parent,0))<0 || qn_attempt("native-subtree-path",1)<0) return -1; errno=0; if(fstatat(qn.slots[parent].fd,name,&current,AT_SYMLINK_NOFOLLOW)<0) { if(errno==ENOENT) return 0; return qn_error("native-subtree-observation",errno); } if(must_be_absent) return qn_error("native-unit-still-present",EBUSY); if(!S_ISDIR(current.st_mode)) return qn_error("native-subtree-kind",EINVAL); if(persistent>=0) { struct qn_version now=qn_stat_version(&current); if(!qn_identity_equal(&now,&qn.slots[persistent].handle_before)) return qn_error("native-subtree-generation",ESTALE); slot=persistent; } else { slot=qn_open_component(parent,name,1,0); if(slot<0) return -1; } if(qn_read_component_text(slot,"cgroup.events",text,sizeof(text),&n)<0) goto done; { char *line=text; int populated=-1; while(*line) { char *end=strchr(line,'\n'); if(!end) { qn_error("native-events-shape",EPROTO); goto done; } *end=0; if(!strncmp(line,"populated ",10)) { if(populated!=-1 || (strcmp(line+10,"0")&&strcmp(line+10,"1"))) { qn_error("native-events-populated-shape",EPROTO); goto done; } populated=line[10]-'0'; } line=end+1; } if(populated!=0) { qn_error("native-subtree-not-empty",EBUSY); goto done; } } if(qn_read_component_text(slot,"cgroup.procs",text,sizeof(text),&n)<0 || n!=0 ||
      qn_read_component_text(slot,"pids.current",text,sizeof(text),&n)<0 || strcmp(text,"0\n")) { qn_error("native-process-debt",EBUSY); goto done; } if(qn_check_slot(slot,0)<0) goto done; result=0; done: if(persistent<0 && slot>=0 && qn_close_slot(slot)<0) result=-1; return result; } static int qn_native_empty(int final) { if((final ? qn.stage!=QN_RETIRED || qn.command_occurrence!=6 || qn.six_calls<4 || qn.six_calls>6 : qn.stage!=QN_TERMINAL) || !qn.prefix_unmounted) return -1;
  /* ENOENT is accepted only through the authentic still-held parent. Every
   * other native error remains unresolved, never an ordinary absence Boolean.
   */ if(qn_empty_directory(qn.common_slot,qn.bootstrap,qn.bootstrap_slot,final)<0 || qn_empty_directory(qn.ancestor_slot,qn.common,qn.common_slot,final)<0) return -1; if(final) qn.stage=QN_RETIRED; return qn_publish_counters(); } static int qn_pipe_slots(int *reader,int *writer) { int fd[2],a=qn_slot_register(-1,0),b=qn_slot_register(-1,0); if(a<0 || b<0 || qn_attempt("pipe2",0)<0) return -1; *reader=a; *writer=b; if(pipe2(fd,O_CLOEXEC|O_NONBLOCK)<0) return qn_error("native-private-pipe",errno); qn.slots[a].fd=fd[0]; qn.slots[b].fd=fd[1]; return 0; } static int qn_capture_one(struct qn_command *c,int stream) { int slot=stream?c->stderr_slot:c->stdout_slot; char **retained=stream?&c->stderr_data:&c->stdout_data; char temporary[QN_CHUNK]; size_t *used=stream?&c->stderr_used:&c->stdout_used; int *eof=stream?&c->stderr_eof:&c->stdout_eof; ssize_t n; size_t selected_limit=c==&qn.commands[8]?(size_t)QN_PROVISION_STREAM:QN_CHUNK; size_t request; if(*eof) return 0; if(*used>selected_limit) return qn_error("native-selected-stream-overflow",EFBIG); request=selected_limit+1-*used; if(!request) return qn_error("native-selected-stream-overflow",EFBIG); if(request>QN_CHUNK) request=QN_CHUNK; if(qn_attempt("native-private-stream-read",0)<0 || request>qn.read_remaining) return -1; if(request>qn.largest_read) qn.largest_read=request; n=read(qn.slots[slot].fd,temporary,request); if(n<0) { if(errno==EAGAIN) return 0; /* No successful acquisition is refunded. */ return qn_error("native-private-stream-read",errno); } qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; if(n) { char *next; if((size_t)n>selected_limit-*used) return qn_error("native-selected-stream-overflow",EFBIG); uint64_t added=(uint64_t)n+(*retained?0:1); uint64_t next_extent=(uint64_t)*used+(uint64_t)n+1; if(added>qn.heap_remaining || next_extent>qn.realloc_peak_remaining) return qn_error("native-output-retention-allocation",ENOSPC); qn.heap_remaining-=added; qn.realloc_peak_remaining-=next_extent; next=realloc(*retained,*used+(size_t)n+1);
    if(!next) return qn_error("native-output-retention-storage",ENOMEM); memcpy(next+*used,temporary,(size_t)n); *retained=next; } else if(!*retained) { if(!qn.heap_remaining) return qn_error("native-empty-stream-allocation",ENOSPC); --qn.heap_remaining; *retained=malloc(1); if(!*retained) return qn_error("native-empty-stream-storage",ENOMEM); } *used+=(size_t)n; if(*used>selected_limit) return qn_error("native-selected-stream-overflow",EFBIG); if(!n) *eof=1; (*retained)[*used]=0; return 0; } static void qn_child_preexec_error(int fd,int native_error) { const unsigned char *p=(const unsigned char *)&native_error; size_t left=sizeof(native_error); unsigned attempts=0; if(native_error<=0) native_error=EIO; while(left && attempts++<sizeof(native_error)) { ssize_t n=write(fd,p,left); if(n<=0) break; p+=(size_t)n; left-=(size_t)n; } _exit(125); } static int qn_command_run(unsigned index,char *const *argv,int startup_transition) { struct qn_command *c; sigset_t block,previous; struct pollfd pollers[4]; int out_w=-1,err_w=-1,gate_r=-1,gate_w=-1,exec_r=-1,exec_w=-1; int saved_mask=0,result=-1,status,exec_errno=0,exec_done=0,launcher=index==8; size_t exec_used=0; int body_negative=0; uint64_t cutoff; ssize_t n; if(index>=QN_SOURCE_COMMAND_COUNT || qn_owner_check(0)<0 || (!startup_transition && qn_complete_startup_check()<0)) return -1; c=&qn.commands[index]; if(c->registered) return qn_error("native-command-occurrence-reuse",EALREADY); memset(c,0,sizeof(*c)); c->registered=1; c->pending=1; c->pid_slot=-1; c->stdout_slot=c->stderr_slot=-1; c->start_ns=qn_clock(); if(!c->start_ns || c->start_ns>UINT64_MAX-UINT64_C(10000000000)) { qn_error("native-command-clock",EINVAL); goto done; } cutoff=launcher?qn.cutoff_ns:c->start_ns+UINT64_C(10000000000); if(cutoff>qn.cutoff_ns) cutoff=qn.cutoff_ns; sigemptyset(&block); sigaddset(&block,SIGCHLD); sigaddset(&block,SIGINT); sigaddset(&block,SIGTERM); sigaddset(&block,SIGHUP); if(qn_attempt("original-Bash-signal-custody",0)<0) goto done; if(sigprocmask(SIG_BLOCK,&block,&previous)<0) {
    qn_error("native-signal-mask",errno); goto done; } saved_mask=1; if((!launcher && (qn_pipe_slots(&c->stdout_slot,&out_w)<0 || qn_pipe_slots(&c->stderr_slot,&err_w)<0)) || qn_pipe_slots(&gate_r,&gate_w)<0 || qn_pipe_slots(&exec_r,&exec_w)<0) goto done; if(qn_attempt("original-fixed-command-fork",0)<0) goto done; c->pid=fork(); if(c->pid<0) { qn_error("original-fixed-command-fork",errno); goto done; } if(c->pid==0) { unsigned char token; struct rlimit fd_limit; int error; ssize_t gate_result; char *const environment[]={"PATH=/usr/bin","LANG=C.UTF-8","LC_ALL=C.UTF-8",0}; extern char **environ;
    /* No Bash callback, allocation, arbitrary executable or QTT import occurs
     * in this trusted fixed native pre-exec prefix. Parent owns every slot and
     * the pending occurrence before fork. Child waits until pidfd/start binding.
     */ if(close(qn.slots[gate_w].fd)<0 || close(qn.slots[exec_r].fd)<0) qn_child_preexec_error(qn.slots[exec_w].fd,errno); if(fcntl(qn.slots[gate_r].fd,F_SETFL,0)<0) qn_child_preexec_error(qn.slots[exec_w].fd,errno); gate_result=read(qn.slots[gate_r].fd,&token,1); if(gate_result<0) qn_child_preexec_error(qn.slots[exec_w].fd,errno); if(gate_result!=1 || token!=0x51) qn_child_preexec_error(qn.slots[exec_w].fd,EPROTO); if(getrlimit(RLIMIT_NOFILE,&fd_limit)<0 || (!launcher && (fcntl(qn.slots[out_w].fd,F_SETFL,0)<0 || fcntl(qn.slots[err_w].fd,F_SETFL,0)<0))) qn_child_preexec_error(qn.slots[exec_w].fd,errno); if(fd_limit.rlim_cur>64) fd_limit.rlim_cur=64; if(fd_limit.rlim_max>64) fd_limit.rlim_max=64; if(setrlimit(RLIMIT_NOFILE,&fd_limit)<0 || (!launcher && (dup2(qn.slots[out_w].fd,STDOUT_FILENO)<0 || dup2(qn.slots[err_w].fd,STDERR_FILENO)<0)) || sigprocmask(SIG_SETMASK,&previous,0)<0) qn_child_preexec_error(qn.slots[exec_w].fd,errno); if(close(qn.slots[gate_r].fd)<0) qn_child_preexec_error(qn.slots[exec_w].fd,errno); execve("/usr/bin/sudo",argv,launcher?environ:environment); error=errno;
    /* Four bytes maximum, no caller-chosen report path. A failed/short write
     * remains an unproven exec prefix when the parent decodes this actual port.
     */ qn_child_preexec_error(qn.slots[exec_w].fd,error); } c->child_created=1; c->pid_slot=qn_pidfd_slot(c->pid); if(c->pid_slot<0 || qn_proc_start(c->pid,&c->start_ticks)<0) goto done; if((!launcher && (qn_close_slot(out_w)<0 || qn_close_slot(err_w)<0)) || qn_close_slot(gate_r)<0 || qn_close_slot(exec_w)<0) goto done; if(qn_gate_write_original(c,gate_w)<0) goto done; if(qn_close_slot(gate_w)<0) goto done; while(!c->terminal || (!launcher&&(!c->stdout_eof||!c->stderr_eof)) || !exec_done) { uint64_t now=qn_clock(); int timeout,ready; if(!now || now>=cutoff) { qn_error("original-native-command-timeout",ETIMEDOUT); goto done; } timeout=(int)((cutoff-now+999999U)/1000000U); if(launcher && qn.bootstrap_slot<0 && timeout>100) timeout=100; pollers[0]=(struct pollfd){launcher||c->stdout_eof?-1:qn.slots[c->stdout_slot].fd,POLLIN,0}; pollers[1]=(struct pollfd){launcher||c->stderr_eof?-1:qn.slots[c->stderr_slot].fd,POLLIN,0}; pollers[2]=(struct pollfd){c->terminal?-1:qn.slots[c->pid_slot].fd,POLLIN,0}; pollers[3]=(struct pollfd){exec_done?-1:qn.slots[exec_r].fd,POLLIN,0}; if(qn_attempt("original-native-command-poll",0)<0) goto done; ready=poll(pollers,4,timeout); if(ready<0) { qn_error("original-native-command-poll",errno); goto done; } if(launcher && qn_hold_bootstrap_if_present()<0) goto done; if(!ready) { if(launcher && qn_clock()<cutoff) continue; qn_error("original-native-command-timeout",ETIMEDOUT); goto done; } if(pollers[0].revents&(POLLIN|POLLHUP)) if(qn_capture_one(c,0)<0) goto done; if(pollers[1].revents&(POLLIN|POLLHUP)) if(qn_capture_one(c,1)<0) goto done; if(!exec_done && (pollers[3].revents&(POLLIN|POLLHUP))) { unsigned char *packet=(unsigned char *)&exec_errno; size_t request=sizeof(exec_errno)-exec_used; unsigned char suffix; n=qn_read(exec_r,request?packet+exec_used:&suffix,request?request:1); if(n<0) goto done; if(n>0) { size_t retained=(size_t)n; if(c->exec_failure_bytes>sizeof(c->exec_failure_raw)-retained) { qn_error("original-exec-port-retained-prefix-overflow",EFBIG); goto done; }
        memcpy(c->exec_failure_raw+c->exec_failure_bytes, request?packet+exec_used:&suffix,retained); c->exec_failure_bytes+=retained; } if(!n) { c->exec_eof=1; if(exec_used==sizeof(exec_errno)) c->exec_failure_errno=exec_errno; if(!exec_used) c->exec_proven=1; else if(exec_used==sizeof(exec_errno) && exec_errno>0) body_negative=1; else { qn_error("original-native-command-exec-port",EPROTO); goto done; } exec_done=1; } else if(request) exec_used+=(size_t)n; else { qn_error("original-native-command-exec-port-suffix",EPROTO); goto done; } } if(!c->terminal && (pollers[2].revents&POLLIN)) { struct qn_terminal_observation *observed=&c->terminal_observation; if(qn_waitid_original(observed,c->pid_slot,"original-native-command-waitid")<0) goto done; if(observed->info.si_pid!=c->pid || observed->info.si_code!=CLD_EXITED) { qn_error("original-native-command-terminal-receipt",EPROTO); goto done; } c->status=observed->info.si_status; c->terminal=1; } { unsigned i; for(i=0;i<4;i++) if(pollers[i].revents&(POLLNVAL|POLLERR)) { qn_error("original-native-command-native-port",EIO); goto done; } } } if(!c->exec_proven || (!launcher&&c->status!=0)) body_negative=1; if(qn_attempt("original-native-command-one-reap",0)<0) goto done; if(waitpid(c->pid,&status,0)!=c->pid || !WIFEXITED(status) || WEXITSTATUS(status)!=c->status) { qn_error("original-native-command-one-reap",errno?errno:EPROTO); goto done; } c->end_ns=qn_clock(); c->pending=0; result=0; if(launcher) qn.stage=QN_TERMINAL; if(body_negative) { qn_error(exec_used?"original-native-command-exec":"original-native-command-nonzero", exec_used?exec_errno:EPROTO); result=-1; } done:
  /* Live/unknown child retains its pidfd and pipe ports. No timeout is converted
   * to terminal, no process-tree kill or unbounded cleanup wait is introduced.
   * Terminal+both actual private EOF is required before any close of its ports.
   */ if(!c->child_created) c->pending=0; /* Actual never-forked native prefix. */ if(c->child_created && c->pending) { qn.stage=QN_HELD; } else { int closed[]={c->stdout_slot,c->stderr_slot,c->pid_slot,out_w,err_w,gate_r,gate_w,exec_r,exec_w}; unsigned i; for(i=0;i<sizeof(closed)/sizeof(closed[0]);i++) if(closed[i]>=0 && !qn.slots[closed[i]].close_attempted && qn_close_slot(closed[i])<0) result=-1; } if(saved_mask) {
    /* Bash SIGCHLD delivery resumes only after exact private-child settlement.
     * On an unresolved child its mask remains held for this holder's lifetime.
     */ if(!c->pending) { if(!qn.calls_remaining) { qn_error("signal-mask-close-allocation",ENOSPC); result=-1; } else { --qn.calls_remaining; ++qn.syscall_calls; if(sigprocmask(SIG_SETMASK,&previous,0)<0) { qn_error("signal-mask-close",errno); result=-1; } } } } return result; } struct qn_manager_fields { char id[65],load[32],transient[8],invocation[33],group[160],active[32]; }; static int qn_manager_decode(const char *raw,struct qn_manager_fields *fields); struct qn_ancestor_origin_fields { char id[65],load[32],transient[8],invocation[33],group[160],active[32],timestamp[21]; }; static int qn_ancestor_origin_readback(unsigned occurrence,struct qn_ancestor_origin_fields *fields) { const char *unit=strrchr(qn.ancestor_group,'/'),*p; unsigned seen=0,index; uint64_t microseconds,origin; struct qn_command *c; char *show[]={"/usr/bin/sudo","-n","--","/usr/bin/systemctl","show","--no-pager","--all",
    "--property=Id,LoadState,Transient,InvocationID,ControlGroup,ActiveState,ActiveEnterTimestampMonotonic",0,0}; if(occurrence>1 || qn.ancestor_slot<0 || !unit || !unit[1] || (occurrence==0 ? qn.stage!=QN_PREPARING || qn.common_slot>=0 : qn.stage!=QN_PREBIRTH || qn.common_slot<0 || qn.bootstrap_slot<0) || qn_check_slot(qn.ancestor_slot,0)<0) return -1; ++unit; show[8]=(char *)unit; index=occurrence==0?QN_ANCESTOR_ORIGIN_BEFORE:QN_ANCESTOR_ORIGIN_AFTER; if(qn_command_run(index,show,0)<0) return -1; c=&qn.commands[index]; if(!c->registered || c->pending || !c->child_created || !c->exec_proven || !c->terminal || c->status || !c->stdout_eof || !c->stderr_eof || c->stderr_used || !c->stdout_used || c->stdout_used>4096 || !c->stdout_data || strlen(c->stdout_data)!=c->stdout_used || c->stdout_data[c->stdout_used-1]!='\n') return qn_error("original-ancestor-origin-command-receipt",EPROTO); memset(fields,0,sizeof(*fields)); p=c->stdout_data; while(*p) { const char *eq=strchr(p,'='),*end=strchr(p,'\n'); unsigned bit=0; char *destination=0; size_t capacity=0,keylen,n,i; if(!eq || !end || eq>=end || eq==p) return qn_error("original-ancestor-origin-field-shape",EPROTO); keylen=(size_t)(eq-p); n=(size_t)(end-eq-1);
#define QN_ORIGIN_FIELD(KEY,MEMBER,BIT) \
    if(keylen==sizeof(KEY)-1 && !memcmp(p,KEY,keylen)) { \
      bit=BIT; destination=fields->MEMBER; capacity=sizeof(fields->MEMBER); }
    QN_ORIGIN_FIELD("Id",id,1U) else QN_ORIGIN_FIELD("LoadState",load,2U) else QN_ORIGIN_FIELD("Transient",transient,4U) else QN_ORIGIN_FIELD("InvocationID",invocation,8U) else QN_ORIGIN_FIELD("ControlGroup",group,16U) else QN_ORIGIN_FIELD("ActiveState",active,32U) else QN_ORIGIN_FIELD("ActiveEnterTimestampMonotonic",timestamp,64U)
#undef QN_ORIGIN_FIELD
    if(!bit || (seen&bit) || !n || n>=capacity) return qn_error("original-ancestor-origin-field-set",EPROTO); for(i=0;i<n;i++) if((unsigned char)eq[1+i]<32 || (unsigned char)eq[1+i]>126 || eq[1+i]=='=') return qn_error("original-ancestor-origin-ascii",EPROTO); memcpy(destination,eq+1,n); destination[n]=0; seen|=bit; p=end+1; } if(seen!=127U || strcmp(fields->id,unit) || strcmp(fields->load,"loaded") || strcmp(fields->transient,"yes") || strcmp(fields->active,"active") || !qn_hex32(fields->invocation) || strcmp(fields->group,qn.ancestor_group) || qn_decimal(fields->timestamp,UINT64_MAX/1000U,&microseconds)<0 || !microseconds) return qn_error("original-ancestor-origin-active-generation",ESTALE); origin=microseconds*1000U; if(origin>UINT64_MAX-QN_DURATION || origin!=qn.origin_ns || qn_check_slot(qn.ancestor_slot,0)<0) return qn_error("same-original-ancestor-origin-and-held-generation",ESTALE); return 0; } static int qn_common_acquire(void) { char *show[]={"/usr/bin/sudo","-n","--","/usr/bin/systemctl","show","--no-pager","--all",
    "--property=Id,LoadState,Transient,InvocationID,ControlGroup,ActiveState",qn.common,0}; struct qn_manager_fields before,after; struct stat named; struct qn_ancestor_origin_fields original_ancestor,after_ancestor; if(qn.stage!=QN_PREPARING || qn.common_attempted || qn_complete_startup_check()<0) return -1;
  /* The original trusted preparation created COMMON before the holder and
   * compiler/loader existed. This owner ADOPTS that live generation; it never
   * issues another StartTransientUnit or accepts a supplied InvocationID.
   * Two actual original readbacks surround physical acquisition. They remain
   * commands 0/1, with independent pending/EOF/terminal native custody.
   */ qn.common_attempted=1;
  /* Earlier trusted preparation owns the BEFORE-controller snapshot. These
   * actual commands rejoin that supplied origin, never resample or certify it.
   */ if(qn_ancestor_origin_readback(0,&original_ancestor)<0) return -1; if(qn_command_run(0,show,0)<0 || qn_manager_decode(qn.commands[0].stdout_data,&before)<0) return -1; if(strcmp(before.id,qn.common) || strcmp(before.load,"loaded") || strcmp(before.transient,"yes") || strcmp(before.active,"active") || !qn_hex32(before.invocation)) return qn_error("original-common-manager-adoption",EPROTO); { char expected[160]; if(snprintf(expected,sizeof(expected),"%s/%s",qn.ancestor_group,qn.common)>=(int)sizeof(expected) || strcmp(before.group,expected)) return qn_error("original-common-manager-cgroup",ESTALE); } if(qn_prebirth(before.invocation)<0 || qn_command_run(1,show,0)<0 || qn_manager_decode(qn.commands[1].stdout_data,&after)<0 || qn_ancestor_origin_readback(1,&after_ancestor)<0) return -1; if(memcmp(&original_ancestor,&after_ancestor,sizeof(original_ancestor))) return qn_error("same-original-ancestor-manager-generation-after-adoption",ESTALE); if(strcmp(after.id,before.id) || strcmp(after.load,before.load) || strcmp(after.transient,before.transient) || strcmp(after.active,before.active) || strcmp(after.invocation,before.invocation) || strcmp(after.group,before.group) || qn_check_slot(qn.ancestor_slot,0)<0 || qn_check_slot(qn.common_slot,0)<0 || qn_fstatat(qn.ancestor_slot,qn.common,&named,"original-common-adopted-name-after")<0) return qn_error("original-common-adopted-generation-after",ESTALE); { struct qn_version current=qn_stat_version(&named); if(!qn_identity_equal(&current,&qn.slots[qn.common_slot].handle_before)) return qn_error("original-common-adopted-handle-after",ESTALE); } if(qn_provision_bind()<0) return -1; return qn_publish_counters(); } static int qn_refresh_after_flag_effect(int number, unsigned long expected) { struct qn_slot *s=&qn.slots[number]; struct stat path,handle; struct qn_version p,h; unsigned long flags; if(qn_fstat(s->fd,&handle,"source-seal-handle-after")<0 || qn_fstatat(s->parent,s->component,&path,"source-seal-path-after")<0 || qn_current_flags(number,&flags)<0) return -1;
  p=qn_stat_version(&path); h=qn_stat_version(&handle); if(flags!=expected || !qn_identity_equal(&p,&s->path_before) || !qn_identity_equal(&h,&s->handle_before) || !qn_identity_equal(&p,&h) || p.mode!=s->path_before.mode || h.mode!=s->handle_before.mode || p.links!=s->path_before.links || h.links!=s->handle_before.links || p.size!=s->path_before.size || h.size!=s->handle_before.size || p.mtime.tv_sec!=s->path_before.mtime.tv_sec || p.mtime.tv_nsec!=s->path_before.mtime.tv_nsec || h.mtime.tv_sec!=s->handle_before.mtime.tv_sec || h.mtime.tv_nsec!=s->handle_before.mtime.tv_nsec) return qn_error("source-seal-permitted-transition-only",ESTALE);
  /* The original tuples remain in qn_input. ONLY the ctime produced by this
   * exact attempted/returned flag transition may enter the held generation.
   * No unrelated byte, extent, mode, link or pathname change is rebaselined.
   */ s->path_before=p; s->handle_before=h; return 0; }
/* Private exact existing-owner role loan. Kind/ordinal are fixed Source calls,
 * never new builtin arguments, wire data or an installation permission rule. */ static int qn_join_path(char *out,const char *parent,const char *name); static int qn_startup_installation_path(const char *path) { size_t n=strlen(QN_SOURCE_INSTALLATION_ROOT); return !strncmp(path,QN_SOURCE_INSTALLATION_ROOT,n) && path[n]=='/'; } static int qn_startup_readonly_file(const char *path) { return qn_startup_installation_path(path) || !strcmp(path,QN_SOURCE_NATIVE_C_PATH) || !strcmp(path,QN_SOURCE_BASH_CONTROLLER_PATH) || !strcmp(path,QN_SOURCE_NATIVE_SO_PATH); } static int qn_startup_roster_path(const char *path) { char tools[QN_PATH]; if(qn_join_path(tools,QN_SOURCE_WORKSPACE,"tools")<0) return -1; return !strcmp(path,QN_SOURCE_INSTALLATION_ROOT) || qn_startup_installation_path(path) || !strcmp(path,QN_SOURCE_WORKSPACE) || !strcmp(path,tools); } static int qn_startup_mode_same_payload(const struct qn_version *before, const struct qn_version *after,mode_t mode) { return qn_identity_equal(before,after) && after->mode==((before->mode&~07777)|mode) && before->links==after->links && before->size==after->size && before->mtime.tv_sec==after->mtime.tv_sec && before->mtime.tv_nsec==after->mtime.tv_nsec; } static int qn_startup_mode_loan(unsigned kind,unsigned ordinal,int number,int restore) { struct qn_startup_mode_loan *j; struct qn_slot *slot; struct stat handle,path; struct qn_version h,p; unsigned long flags; char leaf[64],absolute[QN_PATH]; mode_t expected,wanted; int directory=kind==0; if(kind==0 && ordinal==0) j=&qn.startup_root_loan; else if(kind==1 && ordinal<qn.input_count) j=&qn.inputs[ordinal].startup_baseline_loan; else if(kind==2 && ordinal<qn.catalogue_count) j=&qn.catalogues[ordinal].startup_baseline_loan; else return qn_error("startup-readonly-loan-original-row",EPROTO); if(restore && !j->registered) return 0; /* Legacy/self-protected rows stay unchanged. */ if((restore?qn.stage!=QN_RETIRED:qn.stage!=QN_PREPARING) || !qn.catalogue_attempted ||
      number<0 || (unsigned)number>=qn.slots_used || qn.slots[number].fd<0 || qn.slots[number].close_attempted) return qn_error("startup-readonly-loan-owner-stage",EPROTO); slot=&qn.slots[number]; expected=directory?0700:0600; wanted=directory?0755:0444; if(kind==0) { if(number!=qn.snapshot_root_slot || !S_ISDIR(slot->handle_before.mode)) return qn_error("startup-readonly-loan-exact-control-root",EXDEV); } else { if(slot->parent!=qn.snapshot_root_slot || !S_ISREG(slot->handle_before.mode) || snprintf(leaf,sizeof(leaf),kind==1?"file%u":"directory%u",ordinal)>=(int)sizeof(leaf) || qn_join_path(absolute,QN_SOURCE_SNAPSHOT_ROOT,leaf)<0 || strcmp(leaf,slot->component) || (kind==1 && (!qn_startup_readonly_file(qn.inputs[ordinal].source) || strcmp(absolute,qn.inputs[ordinal].snapshot))) || (kind==2 && (qn_startup_roster_path(qn.catalogues[ordinal].directory)!=1 || strcmp(absolute,qn.catalogues[ordinal].baseline)))) return qn_error("startup-readonly-loan-enumerated-backing",EXDEV); } if(restore) { unsigned i; if(!j->grant_checked || !j->sealed || j->restore_admission || !qn.catalogue_complete) return qn_error("startup-readonly-loan-one-terminal-undo",EALREADY); for(i=0;i<QN_BORROWS;i++) if(qn.borrows[i].registered && !qn.borrows[i].returned) return qn_error("startup-readonly-loan-live-borrower",EBUSY); j->restore_admission=1; /* Original debt before any fallible terminal getter. */ } else { if(j->registered) return qn_error("startup-readonly-loan-single-grant",EALREADY); j->registered=1; j->grant_slot=number; j->grant_admission=1; } if(qn_check_slot(number,directory&&!restore?0:1)<0 || qn_fstat(slot->fd,&handle,"startup-mode-before-handle")<0) return -1; h=qn_stat_version(&handle); if(restore) j->restore_before_handle=h; else { j->before_handle=h; j->uid=handle.st_uid; j->gid=handle.st_gid; } if(qn_fstatat(slot->parent,slot->component,&path,"startup-mode-before-path")<0) return -1; p=qn_stat_version(&path); if(restore) j->restore_before_path=p; else j->before_path=p;
  if(!qn_version_equal(&h,&p) || handle.st_uid!=0 || handle.st_gid!=0 || path.st_uid!=handle.st_uid || path.st_gid!=handle.st_gid || (!directory && handle.st_nlink!=1) || (handle.st_mode&07777)!=(restore?wanted:expected) || qn_current_flags(number,&flags)<0) return qn_error("startup-readonly-loan-true-before",ESTALE); if(restore) { if(handle.st_uid!=j->uid || handle.st_gid!=j->gid || flags!=j->original_flags || !qn_startup_mode_same_payload(&j->protected_handle,&h,wanted) || !qn_startup_mode_same_payload(&j->protected_path,&p,wanted) || (kind==1 && !qn.inputs[ordinal].baseline_restore_attempted) || (kind==2 && !(qn.catalogues[ordinal].restore_attempted&2))) return qn_error("startup-readonly-loan-after-original-flag-undo",ESTALE); } else { j->original_flags=flags; if(flags&FS_IMMUTABLE_FL) return qn_error("startup-readonly-loan-before-immutable",EPERM); } if(qn_attempt(restore?"startup-mode-terminal-undo":"startup-mode-readonly-grant",1)<0) return -1; if(restore) j->restore_dispatched=1; else j->grant_dispatched=1; if(fchmod(slot->fd,restore?expected:wanted)<0) { int error=errno; if(restore) j->restore_errno=error; else j->grant_errno=error; return qn_error("startup-readonly-loan-fchmod",error); } if(restore) j->restore_returned=1; else j->grant_returned=1; if(qn_fstat(slot->fd,&handle,"startup-mode-returned-handle")<0) return -1; h=qn_stat_version(&handle); if(restore) j->restored_handle=h; else j->granted_handle=h; if(qn_fstatat(slot->parent,slot->component,&path,"startup-mode-returned-path")<0) return -1; p=qn_stat_version(&path); if(restore) j->restored_path=p; else j->granted_path=p; if(!qn_version_equal(&h,&p) || handle.st_uid!=j->uid || handle.st_gid!=j->gid || path.st_uid!=j->uid || path.st_gid!=j->gid || !qn_startup_mode_same_payload(restore?&j->restore_before_handle:&j->before_handle, &h,restore?expected:wanted) || !qn_startup_mode_same_payload(restore?&j->restore_before_path:&j->before_path, &p,restore?expected:wanted) || qn_current_flags(number,&flags)<0 || flags!=j->original_flags)
    return qn_error("startup-readonly-loan-returned-generation",ESTALE);
  /* Only this actual returned mode effect may change mode/ctime in held DATA. */ slot->handle_before=h; slot->path_before=p; if(restore) j->restored=1; else { j->grant_checked=1; if(directory) { j->protected_handle=h; j->protected_path=p; j->protected_flags=flags; j->sealed=1; } } return 0; } static int qn_flag_command_quiet(unsigned index) { const struct qn_command *c; const struct qn_terminal_observation *o; if(index>=QN_SOURCE_COMMAND_COUNT) return qn_error("source-seal-command-incidence",EINVAL); c=&qn.commands[index]; o=&c->terminal_observation;
  /* This check follows the actual flag-generation refresh. Attempted/applied
   * effects, all streams and allocation debt stay in the original owner.
   * A noisy native-zero result is HELD; it cannot dispatch another command.
   */ if(!c->registered || !c->child_created || c->pending || !c->exec_proven || !c->exec_eof || !c->terminal || c->status || !c->stdout_eof || !c->stderr_eof || !o->registered || !o->native_attempted || o->result || o->native_errno || o->info.si_pid!=c->pid || o->info.si_code!=CLD_EXITED || o->info.si_status || c->stdout_used || c->stderr_used) return qn_error("source-seal-native-terminal-and-quiet",EPROTO); return 0; } static int qn_flag_effect(unsigned ordinal,int baseline,int restore) { struct qn_input *p; int number,*attempted; unsigned long before,after; unsigned index; char *argv[8]; char *path; int opened=0,result=0; if(ordinal>=qn.input_count || (restore?qn.stage!=QN_RETIRED:qn.stage!=QN_PREPARING)) return -1; p=&qn.inputs[ordinal]; number=baseline?p->snapshot_slot:p->source_slot; path=baseline?p->snapshot:p->source; if(restore) { number=qn_regular_absolute(path); opened=1; if(number<0) return -1; if(!qn_version_equal(&qn.slots[number].path_before, baseline?&p->protected_baseline_path:&p->protected_source_path) || !qn_version_equal(&qn.slots[number].handle_before, baseline?&p->protected_baseline_handle:&p->protected_source_handle)) { qn_error("source-seal-restore-protected-generation",ESTALE); result=-1; goto done; } } before=baseline?p->baseline_original_flags:p->original_flags; after=restore?before:(before|FS_IMMUTABLE_FL); attempted=restore?(baseline?&p->baseline_restore_attempted:&p->source_restore_attempted): (baseline?&p->baseline_seal_attempted:&p->source_seal_attempted); if(*attempted || qn_check_slot(number,1)<0) { qn_error("source-seal-effect-single-use",EALREADY); result=-1; goto done; } *attempted=1; /* Journal debt exists BEFORE the original native effect. */ if(before&FS_IMMUTABLE_FL) { unsigned long current; if(qn_current_flags(number,&current)<0 || current!=before) { qn_error("source-seal-original-protected-generation",ESTALE); result=-1; } goto done; } index=9+4*ordinal+(restore?2:0)+(baseline?1:0); if(index>=QN_SOURCE_COMMAND_COUNT) {
    qn_error("source-seal-command-incidence",ENOSPC); result=-1; goto done; } argv[0]="/usr/bin/sudo"; argv[1]="-n"; argv[2]="--"; argv[3]="/usr/bin/chattr"; argv[4]=restore?"-i":"+i"; argv[5]="--"; argv[6]=path; argv[7]=0;
  /* This is ONLY the already selected original finite SourceSeal helper,
   * over this original registered path/inode. It is not a user argv executor,
   * new privilege setting or a request to modify file mode/ACL/installation.
   */ if(qn_command_run(index,argv,1)<0 || qn_refresh_after_flag_effect(number,after)<0 || qn_flag_command_quiet(index)<0) result=-1; done: if(restore && baseline && result==0 && p->startup_baseline_loan.registered && qn_startup_mode_loan(1,ordinal,number,1)<0) result=-1; if(opened && qn_close_slot(number)<0) result=-1; return result; } static int qn_catalogue_flag_effect(unsigned ordinal,int baseline,int restore) { struct qn_catalogue *c; int slot,*attempted; unsigned long before,after; unsigned index; char *argv[8]; char *path; if(ordinal>=qn.catalogue_count || (restore?qn.stage!=QN_RETIRED:qn.stage!=QN_PREPARING)) return -1; c=&qn.catalogues[ordinal]; slot=baseline?c->baseline_slot:c->directory_slot; path=baseline?c->baseline:c->directory; before=baseline?c->baseline_original_flags:c->original_flags; after=restore?before:(before|FS_IMMUTABLE_FL); attempted=restore?&c->restore_attempted:&c->seal_attempted;
  /* Two operands use two bits in the existing attempted field. */ if((*attempted&(baseline?2:1)) || qn_check_slot(slot,1)<0) return qn_error("source-catalogue-seal-single-use",EALREADY); *attempted|=baseline?2:1; if(before&FS_IMMUTABLE_FL) { unsigned long current; if(qn_current_flags(slot,&current)<0 || current!=before) return qn_error("source-catalogue-original-protection",ESTALE); return 0; } index=9+4*QN_INPUTS+4*ordinal+(restore?2:0)+(baseline?1:0); if(index>=QN_SOURCE_COMMAND_COUNT) return qn_error("source-catalogue-seal-incidence",ENOSPC); argv[0]="/usr/bin/sudo"; argv[1]="-n"; argv[2]="--"; argv[3]="/usr/bin/chattr"; argv[4]=restore?"-i":"+i"; argv[5]="--"; argv[6]=path; argv[7]=0; if(qn_command_run(index,argv,1)<0 || qn_refresh_after_flag_effect(slot,after)<0 || qn_flag_command_quiet(index)<0) return -1; if(restore && baseline && c->startup_baseline_loan.registered) return qn_startup_mode_loan(2,ordinal,slot,1); return 0; } static int qn_catalogue_register(char **a) { struct qn_catalogue *c; struct qn_version dp,dh,bp,bh; uint64_t length; size_t n; const char *p,*previous=0; size_t previous_len=0; if(qn.stage!=QN_PREPARING || qn.catalogue_attempted || qn.catalogue_count>=QN_SOURCE_CATALOGUE_COUNT || qn_expected_version(a[4],&dp)<0 || qn_expected_version(a[5],&dh)<0 || qn_expected_version(a[6],&bp)<0 || qn_expected_version(a[7],&bh)<0 || !S_ISDIR(dp.mode) || !S_ISDIR(dh.mode) || !S_ISREG(bp.mode) || !S_ISREG(bh.mode) || bp.links!=1 || bh.links!=1 || qn_decimal(a[3],QN_CHUNK-1,&length)<0) return -1; c=&qn.catalogues[qn.catalogue_count++]; memset(c,0,sizeof(*c)); c->registered=1; c->directory_slot=c->baseline_slot=-1; snprintf(c->directory,sizeof(c->directory),"%s",a[1]); snprintf(c->baseline,sizeof(c->baseline),"%s",a[2]); c->directory_slot=qn_safe_root(a[1]); c->baseline_slot=qn_regular_absolute(a[2]); if(c->directory_slot<0 || c->baseline_slot<0 || !qn_version_equal(&dp,&qn.slots[c->directory_slot].path_before) || !qn_version_equal(&dh,&qn.slots[c->directory_slot].handle_before) ||
      !qn_version_equal(&bp,&qn.slots[c->baseline_slot].path_before) || !qn_version_equal(&bh,&qn.slots[c->baseline_slot].handle_before) || bp.size<0 || (uint64_t)bp.size!=length || qn_current_flags(c->directory_slot,&c->original_flags)<0 || qn_current_flags(c->baseline_slot,&c->baseline_original_flags)<0) return -1; c->original_path=dp; c->original_handle=dh; c->baseline_path=bp; c->baseline_handle=bh; c->names=malloc((size_t)length+1); if(!c->names) return qn_error("source-catalogue-storage",ENOMEM); if(qn_read_text(c->baseline_slot,c->names,(size_t)length+1,&n)<0 || n!=(size_t)length) return qn_error("source-catalogue-independent-extent",EPROTO); c->names_length=n; p=c->names; while(*p) { const char *end=strchr(p,'\n'); size_t len; if(!end || !(len=(size_t)(end-p)) || len>NAME_MAX || memchr(p,'/',len)) return qn_error("source-catalogue-name-shape",EPROTO); if(previous) { size_t common=previous_len<len?previous_len:len; int compared=memcmp(previous,p,common); if(compared>0 || (!compared && previous_len>=len)) return qn_error("source-catalogue-canonical-membership",EPROTO); } if((len==1&&p[0]=='.') || (len==2&&p[0]=='.'&&p[1]=='.')) return qn_error("source-catalogue-dot-name",EPROTO); previous=p; previous_len=len; ++c->name_count; p=end+1; } if(qn_catalogue_flag_effect((unsigned)qn.catalogue_count-1,0,0)<0 || qn_catalogue_flag_effect((unsigned)qn.catalogue_count-1,1,0)<0 || qn_immutable_slot(c->directory_slot,&c->flags)<0 || qn_immutable_slot(c->baseline_slot,&c->baseline_flags)<0 || qn_catalogue_check(c)<0) return -1; return qn_publish_counters(); } static int qn_absence_register(char **a) { struct qn_absence *absent; struct qn_version expected_path,expected_handle; char parent[QN_PATH]; const char *slash; size_t n; unsigned i; if(qn.stage!=QN_PREPARING || qn.catalogue_attempted || qn.absence_count>=QN_SOURCE_ABSENCE_COUNT || qn_expected_version(a[2],&expected_path)<0 || qn_expected_version(a[3],&expected_handle)<0 || !S_ISDIR(expected_path.mode) || !S_ISDIR(expected_handle.mode) ||
      !a[1] || a[1][0]!='/' || strlen(a[1])>=QN_PATH || !(slash=strrchr(a[1],'/')) || !qn_component(slash+1)) return -1; n=(size_t)(slash-a[1]); if(!n) n=1; memcpy(parent,a[1],n); parent[n]=0; absent=&qn.absences[qn.absence_count++]; memset(absent,0,sizeof(*absent)); absent->registered=1; absent->parent_slot=qn_safe_root(parent); snprintf(absent->component,sizeof(absent->component),"%s",slash+1); if(absent->parent_slot<0 || !qn_version_equal(&expected_path,&qn.slots[absent->parent_slot].path_before) || !qn_version_equal(&expected_handle,&qn.slots[absent->parent_slot].handle_before)) return -1;
  /* A protected, complete original parent catalogue must already cover this
   * negative operand. An absent name cannot grant an unprotected future path.
   */ for(i=0;i<qn.catalogue_count;i++) if(qn_identity_equal(&expected_handle, &qn.slots[qn.catalogues[i].directory_slot].handle_before)) break; if(i==qn.catalogue_count) return qn_error("source-absence-parent-not-protected",EPERM); absent->parent_path=expected_path; absent->parent_handle=expected_handle; return qn_absence_check(absent); }
/* The supplier below is the same finite native preparation owner. It captures
 * the original selected installation and CODE4 prefix before any checker or
 * PROVISION loader. No Python interpreter, import, event decoder, ticket, wire
 * FD or caller-provided file roster is used to discover these operands.
 * Its initial selected native/build/getter primitive and every actual Source
 * allocation must already be admitted; this C body does not issue that grant.
 */ struct qn_native_dirent { uint64_t ino; int64_t offset; unsigned short reclen; unsigned char type; char name[]; }; static int qn_string_compare(const void *a,const void *b) { return strcmp(*(const char *const *)a,*(const char *const *)b); } static int qn_join_path(char *out,const char *parent,const char *name) { int n; if(!parent || parent[0]!='/' || !qn_component(name)) return -1; n=snprintf(out,QN_PATH,"%s%s%s",parent,strcmp(parent,"/")?"/":"",name); return n<0 || n>=QN_PATH ? qn_error("source-selected-path-extent",ENAMETOOLONG):0; } static int qn_snapshot_root_create(void) {
  /* Keep the existing private caller/name. This body independently ADOPTS the
   * genuinely precreated original store; it never accepts EEXIST as creation.
   * The prior expected root DATA remain distinct from this current readback.
   * Original prior-holder/protection custody is an upstream Source premise,
   * not a successful flag issued by this metadata operation.
   */ char parent[QN_PATH]; const char *slash; int directory,number; size_t n; struct stat path,handle; if(qn.pid!=getpid() || qn.tid!=(pid_t)syscall(SYS_gettid)) return -1; if(qn.snapshot_root_adopt_attempted) return qn_error("startup-original-root-adoption-single-use",EALREADY); qn.snapshot_root_adopt_attempted=1; qn.snapshot_root_adopt_slot=-1; qn.snapshot_root_adopt_slots_begin=qn.slots_used; /* Original partial-slot range, before fallibility. */ if(qn_owner_check(0)<0 || qn.stage!=QN_PREPARING || !qn.catalogue_attempted || qn.snapshot_root_slot>=0) return qn_error("startup-original-root-adoption-caller",EPROTO); if(QN_SOURCE_SNAPSHOT_ROOT[0]!='/' || !(slash=strrchr(QN_SOURCE_SNAPSHOT_ROOT,'/')) || !slash[1] || strlen(QN_SOURCE_SNAPSHOT_ROOT)>=QN_PATH || !qn_component(slash+1)) return qn_error("startup-original-root-adoption-locator",EINVAL); n=(size_t)(slash-QN_SOURCE_SNAPSHOT_ROOT); if(!n) n=1; memcpy(parent,QN_SOURCE_SNAPSHOT_ROOT,n); parent[n]=0; directory=qn_safe_root(parent); if(directory<0) return -1; number=qn_open_component(directory,slash+1,1,0); qn.snapshot_root_adopt_slot=number;
  /* On a negative helper return, registered partial slots at or beyond the
   * original slots_begin still retain every actual FD/error/close debt. */ if(number<0) return -1; if(qn_fstat(qn.slots[number].fd,&handle,"startup-original-root-adopt-handle")<0 || qn_fstatat(directory,slash+1,&path,"startup-original-root-adopt-path")<0) return -1; if((uintmax_t)handle.st_dev!=qn_prior_snapshot_root.dev || (uintmax_t)path.st_dev!=qn_prior_snapshot_root.dev || (uintmax_t)handle.st_ino!=qn_prior_snapshot_root.ino || (uintmax_t)path.st_ino!=qn_prior_snapshot_root.ino || (uintmax_t)handle.st_mode!=qn_prior_snapshot_root.mode || (uintmax_t)path.st_mode!=qn_prior_snapshot_root.mode || (uintmax_t)handle.st_uid!=qn_prior_snapshot_root.uid || (uintmax_t)path.st_uid!=qn_prior_snapshot_root.uid || (uintmax_t)handle.st_gid!=qn_prior_snapshot_root.gid || (uintmax_t)path.st_gid!=qn_prior_snapshot_root.gid || handle.st_uid!=geteuid() || qn_check_slot(number,1)<0) return qn_error("startup-original-root-prior-path-handle-generation",ESTALE);
  /* Publication is after complete independent identity/permission readback.
   * Root directory size/mtime/ctime are NOT substituted as historical expected
   * values: original controlled compiler/source additions change them. Their
   * actual prior transition journal/lifetime remains with the genuine preparer.
   * Existing slots retain this operation's stable before/after metadata only.
   */ qn.snapshot_root_slot=number; return 0; } static int qn_write_slot(int number,const void *buffer,size_t extent) { const unsigned char *p=buffer; size_t offset=0; while(offset<extent) { size_t request=extent-offset; ssize_t written; if(request>QN_CHUNK) request=QN_CHUNK; if(request>qn.write_remaining || qn_attempt("startup-baseline-write",0)<0) return -1; if(request>qn.largest_write) qn.largest_write=request; written=write(qn.slots[number].fd,p+offset,request); if(written<0) return qn_error("startup-baseline-write",errno); if(!written) return qn_error("startup-baseline-zero-write",EIO); qn.write_remaining-=(uint64_t)written; qn.write_bytes+=(uint64_t)written; offset+=(size_t)written; } return 0; } static int qn_baseline_create_at(int parent_root_slot,const char *parent_root_path, const char *name,int source,const char *literal, uint64_t length,char *absolute) { int writer=-1,reader=-1,result=-1; struct stat path,handle; struct qn_version original; unsigned char chunk[QN_CHUNK],extra; uint64_t remaining=length; ssize_t n; if(parent_root_slot<0 || !qn_component(name) || qn_join_path(absolute,parent_root_path,name)<0) return -1; writer=qn_slot_register(parent_root_slot,name); if(writer<0) return -1; if(qn_attempt("startup-baseline-create-new",0)<0) goto done; qn.slots[writer].fd=openat(qn.slots[parent_root_slot].fd,name, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600); if(qn.slots[writer].fd<0) { qn_error("startup-baseline-create-new",errno); goto done; } if(qn_fstat(qn.slots[writer].fd,&handle,"startup-baseline-new-handle")<0 || !S_ISREG(handle.st_mode) || handle.st_nlink!=1 || handle.st_size!=0 || handle.st_uid!=geteuid() || (handle.st_mode&0777)!=0600) { qn_error("startup-baseline-creation-policy",EPERM); goto done; } if(source>=0) { if(qn_check_slot(source,1)<0 || qn_seek_start(source)<0) goto done; original=qn.slots[source].handle_before; while(remaining) { size_t request=remaining>QN_CHUNK?QN_CHUNK:(size_t)remaining; n=qn_read(source,chunk,request); if(n<0) goto done;
      if(!n) { qn_error("startup-original-capture-truncation",EIO); goto done; } if(qn_write_slot(writer,chunk,(size_t)n)<0) goto done; remaining-=(uint64_t)n; } n=qn_read(source,&extra,1); if(n<0) goto done; if(n || qn_check_slot(source,1)<0 || !qn_version_equal(&original,&qn.slots[source].handle_before)) { qn_error("startup-original-capture-suffix-or-generation",ESTALE); goto done; } } else if(!literal || length>SIZE_MAX || qn_write_slot(writer,literal,(size_t)length)<0) goto done; if(qn_attempt("startup-baseline-fsync",0)<0 || fsync(qn.slots[writer].fd)<0) { qn_error("startup-baseline-fsync",errno); goto done; } if(qn_fstat(qn.slots[writer].fd,&handle,"startup-baseline-written-handle")<0 || qn_fstatat(parent_root_slot,name,&path,"startup-baseline-written-path")<0 || !S_ISREG(handle.st_mode) || handle.st_nlink!=1 || handle.st_size<0 || (uint64_t)handle.st_size!=length || path.st_dev!=handle.st_dev || path.st_ino!=handle.st_ino || path.st_mode!=handle.st_mode || path.st_nlink!=1) { qn_error("startup-baseline-path-handle-written-generation",ESTALE); goto done; } qn.slots[writer].path_before=qn_stat_version(&path); qn.slots[writer].handle_before=qn_stat_version(&handle); if(qn_close_slot(writer)<0) goto done; reader=qn_open_component(parent_root_slot,name,0,1); if(reader<0) goto done; if(!qn_version_equal(&qn.slots[reader].path_before,&qn.slots[writer].path_before) || !qn_version_equal(&qn.slots[reader].handle_before,&qn.slots[writer].handle_before)) { qn_error("startup-baseline-reopened-generation",ESTALE); goto done; } result=reader; done: if(writer>=0 && !qn.slots[writer].close_attempted && qn_close_slot(writer)<0) result=-1; if(result<0 && reader>=0 && qn_close_slot(reader)<0) result=-1;
  /* Failed/partial create-new files remain original evidence, never replaced,
   * blindly reused or broadly removed on a later capture attempt.
   */ return result; } static int qn_baseline_create(const char *name,int source,const char *literal, uint64_t length,char *absolute) { return qn_baseline_create_at(qn.snapshot_root_slot,QN_SOURCE_SNAPSHOT_ROOT, name,source,literal,length,absolute); }  static int qn_plan_file(const char *absolute) { struct qn_input *p; struct stat st; int slot=-1,result=-1; unsigned i; if(qn.input_count>=QN_INPUTS) return qn_error("source-startup-file-count",ENOSPC); slot=qn_regular_absolute(absolute); if(slot<0) return -1; if(qn_fstat(qn.slots[slot].fd,&st,"startup-plan-file-handle")<0 || st.st_size<0 || (uint64_t)st.st_size>(UINT64_C(128)<<20)) goto done; for(i=0;i<qn.input_count;i++) if(qn_identity_equal(&qn.inputs[i].source_version, &qn.slots[slot].handle_before)) {
    /* A repeated selected physical payload is accounted once; distinct alias
     * filename observations stay in their original protected alias rows.
     */ if(strcmp(qn.inputs[i].source,absolute)) { qn_error("startup-unselected-physical-alias",EXDEV); goto done; } result=0; goto done; } if((uint64_t)st.st_size>UINT64_MAX-qn.payload_bytes) { qn_error("startup-plan-byte-overflow",EOVERFLOW); goto done; } p=&qn.inputs[qn.input_count++]; memset(p,0,sizeof(*p)); p->occupied=1; p->source_slot=p->snapshot_slot=-1; p->length=(uint64_t)st.st_size; snprintf(p->source,sizeof(p->source),"%s",absolute); p->source_version=qn.slots[slot].handle_before; p->protected_source_path=qn.slots[slot].path_before; p->protected_source_handle=qn.slots[slot].handle_before; qn.payload_bytes+=p->length; result=0; done: if(slot>=0 && qn_close_slot(slot)<0) result=-1; return result; } static int qn_plan_alias(int parent,const char *path,const char *name) { struct qn_alias *a; struct stat before,after; ssize_t n; struct qn_version bv,av; if(qn.alias_count>=QN_SOURCE_ALIAS_COUNT || qn_fstatat(parent,name,&before,
      "startup-alias-path-before")<0 || !S_ISLNK(before.st_mode)) return -1; a=&qn.aliases[qn.alias_count++]; memset(a,0,sizeof(*a)); a->registered=1; a->parent_slot=parent; snprintf(a->path,sizeof(a->path),"%s",path); snprintf(a->name,sizeof(a->name),"%s",name); bv=qn_stat_version(&before); if(qn_attempt("startup-alias-readlinkat",0)<0 || QN_PATH-1>qn.read_remaining) return -1; n=readlinkat(qn.slots[parent].fd,name,a->target,QN_PATH-1); if(n<0) return qn_error("startup-alias-readlinkat",errno); qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; if(qn.largest_read<QN_PATH-1) qn.largest_read=QN_PATH-1; if(!n || n==QN_PATH-1 || memchr(a->target,0,(size_t)n) || qn_fstatat(parent,name,&after,"startup-alias-path-after")<0) return -1; av=qn_stat_version(&after); if(!qn_version_equal(&bv,&av)) return qn_error("startup-alias-generation-changed",ESTALE); a->target[n]=0; a->length=(size_t)n; a->original=bv; return 0; } static int qn_plan_directory(const char *path,unsigned depth,int recurse) { struct qn_catalogue *c; char **names=0; size_t count=0,capacity=0,total=0; unsigned char entries[QN_CHUNK]; int directory,result=-1; unsigned i; ssize_t n; if(depth>64 || qn.catalogue_count>=QN_SOURCE_CATALOGUE_COUNT) return qn_error("startup-plan-directory-bound",ENOSPC); directory=qn_safe_root(path); if(directory<0) return -1; for(i=0;i<qn.catalogue_count;i++) if(qn_identity_equal(&qn.catalogues[i].original_handle, &qn.slots[directory].handle_before)) return 0; c=&qn.catalogues[qn.catalogue_count++]; memset(c,0,sizeof(*c)); c->registered=1; c->directory_slot=directory; c->baseline_slot=-1; snprintf(c->directory,sizeof(c->directory),"%s",path); c->original_path=qn.slots[directory].path_before; c->original_handle=qn.slots[directory].handle_before; if(qn_current_flags(directory,&c->original_flags)<0 || qn_seek_start(directory)<0) goto done; for(;;) { size_t at=0; if(qn_attempt("startup-plan-getdents64",0)<0 || QN_CHUNK>qn.read_remaining) goto done; n=syscall(SYS_getdents64,qn.slots[directory].fd,entries,QN_CHUNK);
    if(n<0) { qn_error("startup-plan-getdents64",errno); goto done; } qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; if(qn.largest_read<QN_CHUNK) qn.largest_read=QN_CHUNK; if(!n) break; while(at<(size_t)n) { struct qn_native_dirent *e=(struct qn_native_dirent *)(entries+at); size_t length; if((size_t)n-at<offsetof(struct qn_native_dirent,name)+1 || e->reclen<offsetof(struct qn_native_dirent,name)+1 || e->reclen>(size_t)n-at || !memchr(e->name,0,e->reclen - offsetof(struct qn_native_dirent,name))) { qn_error("startup-plan-getdents-shape",EPROTO); goto done; } at+=e->reclen; if(!strcmp(e->name,".") || !strcmp(e->name,"..")) continue; length=strlen(e->name); if(!qn_component(e->name) || memchr(e->name,'\n',length) || length+1>QN_CHUNK-1-total) { qn_error("startup-plan-roster-shape",ENOSPC); goto done; } if(count==capacity) { size_t next=capacity?capacity*2:16; char **grown; if(next<count || next>65536 || (next-capacity)*sizeof(*names)>qn.heap_remaining) goto done; qn.heap_remaining-=(next-capacity)*sizeof(*names); grown=realloc(names,next*sizeof(*names)); if(!grown) goto done; names=grown; capacity=next; } if(length+1>qn.heap_remaining) goto done; qn.heap_remaining-=length+1; names[count]=malloc(length+1); if(!names[count]) goto done; memcpy(names[count],e->name,length+1); ++count; total+=length+1; } } if(qn_check_slot(directory,1)<0 || total+1>qn.heap_remaining) goto done; qn.heap_remaining-=total+1; c->names=malloc(total+1); if(!c->names) goto done; qsort(names,count,sizeof(*names),qn_string_compare); total=0; for(i=0;i<count;i++) { size_t length=strlen(names[i]); char absolute[QN_PATH]; struct stat st; if(i && !strcmp(names[i-1],names[i])) { qn_error("startup-plan-duplicate-name",EPROTO); goto done; } memcpy(c->names+total,names[i],length); c->names[total+length]='\n'; total+=length+1; if(qn_join_path(absolute,path,names[i])<0 || qn_fstatat(directory,names[i],&st,"startup-plan-child-kind")<0) goto done; if(S_ISLNK(st.st_mode)) { if(qn_plan_alias(directory,absolute,names[i])<0) goto done;
    } else if(recurse && S_ISDIR(st.st_mode)) { if(qn_plan_directory(absolute,depth+1,1)<0) goto done; } else if(recurse && S_ISREG(st.st_mode)) { if(qn_plan_file(absolute)<0) goto done; } else if(!S_ISDIR(st.st_mode) && !S_ISREG(st.st_mode)) { qn_error("startup-plan-unsupported-node",EINVAL); goto done; } } c->names[total]=0; c->names_length=total; c->name_count=count; if(total>UINT64_MAX-qn.roster_bytes) goto done; qn.roster_bytes+=total; result=0; done: for(i=0;i<count;i++) free(names[i]); free(names); return result; } static int qn_aliases_check(void) { unsigned i; char target[QN_PATH]; struct stat st; struct qn_version now; ssize_t n; for(i=0;i<qn.alias_count;i++) { struct qn_alias *a=&qn.aliases[i]; if(qn_check_slot(a->parent_slot,1)<0 || qn_fstatat(a->parent_slot,a->name,&st,"startup-alias-recheck")<0) return -1; now=qn_stat_version(&st); if(!qn_version_equal(&now,&a->original) || !S_ISLNK(st.st_mode) || qn_attempt("startup-alias-target-recheck",0)<0 || QN_PATH-1>qn.read_remaining) return -1; n=readlinkat(qn.slots[a->parent_slot].fd,a->name,target,QN_PATH-1); if(n<0) return qn_error("startup-alias-target-recheck",errno); qn.read_remaining-=(uint64_t)n; qn.read_bytes+=(uint64_t)n; if(n!=(ssize_t)a->length || memcmp(target,a->target,a->length)) return qn_error("startup-alias-target-changed",ESTALE); } return 0; } static int qn_capture_startup(void) { unsigned i; int left=-1,right=-1,result=-1; uint64_t demand,available; struct statvfs volume; char name[64]; const char *const code6[]={
    "run_validation_gates.py","validation_reliability.py",
    "validation_scope_registry.py","ci_branch_context.py",
    "validation_inventory.py","repo_path_refs.py"};
  /* Fixed original file operands; actual compiler vector/macros must join the
   * genuine original pre-build protected Source record before first loader. */ const char *const original_native_policy_inputs[]={ QN_SOURCE_WORKFLOW_PATH,QN_SOURCE_BASH_CONTROLLER_PATH, QN_SOURCE_NATIVE_C_PATH,QN_SOURCE_NATIVE_SO_PATH, QN_SOURCE_POLICY_BASE,QN_SOURCE_POLICY_CONFIG,QN_SOURCE_POLICY_FEATURES}; char tools[QN_PATH],absolute[QN_PATH]; if(qn_owner_check(0)<0 || qn.stage!=QN_PREPARING || qn.catalogue_attempted) return qn_error("startup-capture-single-use",EALREADY); qn.catalogue_attempted=1; if(qn_join_path(tools,QN_SOURCE_WORKSPACE,"tools")<0 || qn_plan_directory(QN_SOURCE_INSTALLATION_ROOT,0,1)<0 || qn_plan_directory(QN_SOURCE_WORKSPACE,0,0)<0 || qn_plan_directory(tools,0,0)<0) return -1; for(i=0;i<6;i++) if(qn_join_path(absolute,tools,code6[i])<0 || qn_plan_file(absolute)<0) return -1; for(i=0;i<sizeof(original_native_policy_inputs)/sizeof(original_native_policy_inputs[0]);i++) if(qn_plan_file(original_native_policy_inputs[i])<0) return -1; if(!qn.input_count || qn.payload_bytes>UINT64_MAX-qn.roster_bytes || (demand=qn.payload_bytes+qn.roster_bytes)>QN_SOURCE_STORAGE_BYTES || demand>qn.write_remaining || demand>UINT64_MAX-UINT64_C(1073741824) || qn_snapshot_root_create()<0 || qn_attempt("startup-caller-available-space",1)<0) return -1; if(fstatvfs(qn.slots[qn.snapshot_root_slot].fd,&volume)<0 || !volume.f_frsize || (uint64_t)volume.f_bavail>UINT64_MAX/(uint64_t)volume.f_frsize) return -1; available=(uint64_t)volume.f_bavail*(uint64_t)volume.f_frsize; if(available<demand+UINT64_C(1073741824)) return qn_error("startup-space-floor",ENOSPC);
  /* Protect complete namespace rosters before source-file use. The independent
   * roster backing and its bytes are acquired from the original earlier walk;
   * no current metadata is substituted for an unexplained changed generation.
   */ for(i=0;i<qn.catalogue_count;i++) { struct qn_catalogue *c=&qn.catalogues[i]; if(qn_check_slot(c->directory_slot,1)<0) goto done; snprintf(name,sizeof(name),"directory%u",i); c->baseline_slot=qn_baseline_create(name,-1,c->names,c->names_length,c->baseline); if(c->baseline_slot<0 || qn_current_flags(c->baseline_slot,&c->baseline_original_flags)<0) goto done; if(qn_startup_mode_loan(2,i,c->baseline_slot,0)<0) goto done; c->baseline_path=qn.slots[c->baseline_slot].path_before; c->baseline_handle=qn.slots[c->baseline_slot].handle_before; if(qn_catalogue_flag_effect(i,0,0)<0 || qn_catalogue_flag_effect(i,1,0)<0 || qn_immutable_slot(c->directory_slot,&c->flags)<0 || qn_immutable_slot(c->baseline_slot,&c->baseline_flags)<0 || qn_catalogue_check(c)<0) goto done; c->startup_baseline_loan.protected_path=qn.slots[c->baseline_slot].path_before; c->startup_baseline_loan.protected_handle=qn.slots[c->baseline_slot].handle_before; c->startup_baseline_loan.protected_flags=c->baseline_flags; c->startup_baseline_loan.sealed=1; } for(i=0;i<qn.input_count;i++) { struct qn_input *p=&qn.inputs[i]; left=qn_regular_absolute(p->source); p->source_slot=left; if(left<0 || !qn_version_equal(&p->protected_source_path,&qn.slots[left].path_before) || !qn_version_equal(&p->protected_source_handle,&qn.slots[left].handle_before) || qn_current_flags(left,&p->original_flags)<0 || qn_flag_effect(i,0,0)<0 || qn_immutable_slot(left,&p->flags)<0) goto done; p->protected_source_path=qn.slots[left].path_before; p->protected_source_handle=qn.slots[left].handle_before; snprintf(name,sizeof(name),"file%u",i); right=qn_baseline_create(name,left,0,p->length,p->snapshot); p->snapshot_slot=right; if(right<0 || qn_current_flags(right,&p->baseline_original_flags)<0) goto done; if(qn_startup_readonly_file(p->source) && qn_startup_mode_loan(1,i,right,0)<0) goto done; p->snapshot_version=qn.slots[right].handle_before; if(qn_flag_effect(i,1,0)<0 || qn_immutable_slot(right,&p->baseline_flags)<0 || qn_compare_slots(left,right,p->length)<0) goto done;
    p->protected_baseline_path=qn.slots[right].path_before; p->protected_baseline_handle=qn.slots[right].handle_before; if(p->startup_baseline_loan.registered) { p->startup_baseline_loan.protected_path=p->protected_baseline_path; p->startup_baseline_loan.protected_handle=p->protected_baseline_handle; p->startup_baseline_loan.protected_flags=p->baseline_flags; p->startup_baseline_loan.sealed=1; } if(qn_close_slot(right)<0) { right=-1; goto done; } right=-1; p->snapshot_slot=-1; if(qn_close_slot(left)<0) { left=-1; goto done; } left=-1; p->source_slot=-1; } if(qn_aliases_check()<0 || qn_startup_mode_loan(0,0,qn.snapshot_root_slot,0)<0) goto done; qn.catalogue_complete=1; if(qn_complete_startup_check()<0) goto done; result=qn_publish_counters(); done: if(right>=0 && !qn.slots[right].close_attempted && qn_close_slot(right)<0) result=-1; if(left>=0 && !qn.slots[left].close_attempted && qn_close_slot(left)<0) result=-1; return result; }  static int qn_manager_decode(const char *raw,struct qn_manager_fields *fields) { const char *p=raw; unsigned seen=0; memset(fields,0,sizeof(*fields)); while(*p) { const char *eq=strchr(p,'='),*end=strchr(p,'\n'); unsigned bit=0; char *destination=0; size_t capacity=0,keylen,n; if(!eq || !end || eq>end || eq==p) return qn_error("original-manager-field-shape",EPROTO); keylen=(size_t)(eq-p); n=(size_t)(end-eq-1);
#define QN_FIELD(KEY,MEMBER,BIT) \
    if(keylen==sizeof(KEY)-1 && !memcmp(p,KEY,keylen)) { \
      bit=BIT; destination=fields->MEMBER; capacity=sizeof(fields->MEMBER); }
    QN_FIELD("Id",id,1U) else QN_FIELD("LoadState",load,2U) else QN_FIELD("Transient",transient,4U) else QN_FIELD("InvocationID",invocation,8U) else QN_FIELD("ControlGroup",group,16U) else QN_FIELD("ActiveState",active,32U)
#undef QN_FIELD
    if(!bit || (seen&bit) || n>=capacity) return qn_error("original-manager-field-set",EPROTO); { size_t i; for(i=0;i<n;i++) if((unsigned char)eq[1+i]>127 || !eq[1+i]) return qn_error("original-manager-nonascii",EPROTO); } memcpy(destination,eq+1,n); destination[n]=0; seen|=bit; p=end+1; } return seen==63U?0:qn_error("original-manager-field-coverage",EPROTO); } static int qn_provision_environment_one(const char *name,int required) { SHELL_VAR *v=find_variable_noref(name); const char *value; size_t a,n; char *entry; struct qn_provision *p=&qn.provision; if(!v) return required?qn_error("provision-original-control-absent",ENOENT):0; if(!exported_p(v) || array_p(v) || assoc_p(v) || nameref_p(v) || v->dynamic_value || v->assign_func || !(value=value_cell(v))) return qn_error("provision-original-control-kind",EINVAL); a=strlen(name); n=strnlen(value,QN_DATA); if(n==QN_DATA || a+1>SIZE_MAX-n-1 || p->environment_count>=25 || a+n+2>qn.heap_remaining) return qn_error("provision-original-control-allocation",ENOSPC); qn.heap_remaining-=a+n+2; entry=malloc(a+n+2); if(!entry) return qn_error("provision-original-control-storage",ENOMEM); p->environment[p->environment_count++]=entry; memcpy(entry,name,a); entry[a]='='; memcpy(entry+a+1,value,n+1); p->environment[p->environment_count]=0; return 0; } static const char *qn_provision_environment_value(const char *name) { size_t n=strlen(name),i; for(i=0;i<qn.provision.environment_count;i++) { const char *value=qn.provision.environment[i]; if(!strncmp(value,name,n) && value[n]=='=') return value+n+1; } return 0; } static int qn_provision_original_inputs(void) { static const char *const controls[]={"GITHUB_ACTIONS","GITHUB_EVENT_NAME",
    "GITHUB_REPOSITORY","GITHUB_WORKSPACE","GITHUB_EVENT_PATH","RUNNER_TEMP",
    "GITHUB_REF","GITHUB_REF_NAME","GITHUB_SHA","GITHUB_HEAD_REF","GITHUB_BASE_REF",
    "GITHUB_RUN_ID","GITHUB_RUN_ATTEMPT"}; static const char *const optional[]={"PATH","HOME","SHELL","USER","LOGNAME",
    "LANG","LC_ALL","LC_CTYPE","TZ","QTT_FORCE_FULL_VALIDATION","LD_LIBRARY_PATH"}; struct qn_provision *p=&qn.provision; struct passwd account,*actual=0; char scratch[QN_CHUNK],candidate[QN_PATH],directory[QN_PATH]; struct stat workspace,image; int root=-1,error; unsigned i,depth; for(i=0;i<sizeof(controls)/sizeof(*controls);i++) if(qn_provision_environment_one(controls[i],1)<0) return -1; if(qn_provision_environment_one("GITHUB_OUTPUT",1)<0) return -1; for(i=0;i<sizeof(optional)/sizeof(*optional);i++) if(qn_provision_environment_one(optional[i],0)<0) return -1; if(strcmp(qn_provision_environment_value("GITHUB_WORKSPACE"),QN_SOURCE_WORKSPACE)) return qn_error("provision-original-workspace-selection",ESTALE); root=qn_safe_root(QN_SOURCE_WORKSPACE); if(root<0 || qn_fstat(qn.slots[root].fd,&workspace,"provision-qualified-workspace-account")<0) return -1;
  /* Source-selected NORMAL account comes from the qualified original
   * workspace UID and trusted NSS account. Its primary gid is NOT a claim
   * about historical getgid(), and installation ownership is irrelevant.
   */ if(!workspace.st_uid || qn_attempt("provision-trusted-normal-account",1)<0) return qn_error("provision-normal-account-selection",EINVAL); error=getpwuid_r(workspace.st_uid,&account,scratch,sizeof(scratch),&actual); if(error || !actual || actual!=&account || account.pw_uid!=workspace.st_uid) return qn_error("provision-trusted-normal-account",error?error:ENOENT); p->selected_uid=account.pw_uid; p->selected_gid=account.pw_gid;
  /* Actual inherited parent DIRECTORY only. The future PID root is created
   * by this original parent after fork; no post-fork root FD is inherited. */ p->root_parent=qn_safe_root(qn_provision_environment_value("RUNNER_TEMP")); if(p->root_parent<0) return -1;
  /* qn_safe_root may return an existing retained catalogue parent. This
   * original shared directory slot stays owned until reverse-order close. */ if(qn_join_path(directory,QN_SOURCE_INSTALLATION_ROOT,"bin")<0 || qn_join_path(candidate,directory,"python")<0) return -1;
  /* Resolve only genuine aliases retained in the complete original startup
   * catalogue. The actual terminal image must be one of its protected files.
   */ for(depth=0;depth<40;depth++) { struct qn_alias *alias=0; char next[QN_PATH],parent[QN_PATH],*slash; for(i=0;i<qn.alias_count;i++) if(!strcmp(qn.aliases[i].path,candidate)) { alias=&qn.aliases[i]; break; } if(!alias) break; if(alias->target[0]=='/') { if(strlen(alias->target)>=sizeof(next)) return qn_error("provision-image-alias-extent",ENAMETOOLONG); strcpy(next,alias->target); } else { strcpy(parent,candidate); slash=strrchr(parent,'/'); if(!slash) return qn_error("provision-image-alias-parent",EPROTO); *slash=0; if(qn_join_path(next,parent,alias->target)<0) return -1; }
    /* qn_regular_absolute rejects dot components. A baseline with a different
     * genuine alias form must provide the Source-selected canonical image;
     * no unheld path or followed-current alias is silently accepted.
     */ strcpy(candidate,next); } if(depth==40) return qn_error("provision-image-alias-cycle",ELOOP); for(i=0;i<qn.input_count;i++) if(!strcmp(qn.inputs[i].source,candidate)) break; if(i==qn.input_count) return qn_error("provision-image-not-original-input",ENOENT); p->image_slot=qn_regular_absolute(candidate); if(p->image_slot<0 || !qn_version_equal(&qn.slots[p->image_slot].path_before, &qn.inputs[i].protected_source_path) || !qn_version_equal(&qn.slots[p->image_slot].handle_before, &qn.inputs[i].protected_source_handle) || qn_fstat(qn.slots[p->image_slot].fd,&image,"provision-original-image")<0 || !S_ISREG(image.st_mode) || !(image.st_mode&0111)) return qn_error("provision-image-generation",ESTALE); strcpy(p->image,candidate); if(qn_join_path(directory,QN_SOURCE_WORKSPACE,"tools")<0 || qn_join_path(p->script,directory,"run_validation_gates.py")<0) return -1; for(i=0;i<qn.input_count;i++) if(!strcmp(qn.inputs[i].source,p->script)) break; if(i==qn.input_count) return qn_error("provision-script-not-original-input",ENOENT); if(qn_complete_startup_check()<0) return -1; return 0; } static int qn_provision_directory(int parent,const char *name,unsigned ordinal) { struct qn_provision *p=&qn.provision; struct stat st,path; struct qn_version handle,named; int root; if(ordinal>=3 || p->root_attempted[ordinal]) return qn_error("provision-original-directory-single-use",EALREADY); p->root_attempted[ordinal]=1; p->root_slots[ordinal]=-1; if(qn_attempt("provision-original-directory-mkdir",1)<0 || mkdirat(qn.slots[parent].fd,name,0700)<0) return qn_error("provision-original-directory-mkdir",errno); root=qn_open_component(parent,name,1,0); p->root_slots[ordinal]=root; if(root<0 || qn_attempt("provision-original-directory-ownership",1)<0 || fchown(qn.slots[root].fd,p->selected_uid,p->selected_gid)<0 || qn_attempt("provision-original-directory-mode",1)<0 || fchmod(qn.slots[root].fd,0700)<0 || qn_fstat(qn.slots[root].fd,&st,"provision-original-directory-final")<0 ||
      qn_fstatat(parent,name,&path,"provision-original-directory-path-final")<0) return -1; handle=qn_stat_version(&st); named=qn_stat_version(&path); if(st.st_uid!=p->selected_uid || st.st_gid!=p->selected_gid || path.st_uid!=p->selected_uid || path.st_gid!=p->selected_gid || !S_ISDIR(st.st_mode) || (st.st_mode&07777)!=0700 || !qn_version_equal(&handle,&named)) return qn_error("provision-original-directory-generation",ESTALE);
  /* These versions follow ONLY this journaled create/owner/mode transition. */ qn.slots[root].handle_before=handle; qn.slots[root].path_before=named; p->root_created[ordinal]=1; return root; } static int qn_provision_role_root(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; const char *temporary=qn_provision_environment_value("RUNNER_TEMP"); int parent,root,prefix; if(!temporary || temporary[0]!='/' || c->pid<=0) return qn_error("provision-original-role-root-selection",EINVAL); parent=p->root_parent; if(parent<0 || (unsigned)parent>=qn.slots_used || qn.slots[parent].fd<0 || qn.slots[parent].close_attempted || qn_check_held_parent(parent)<0) return -1; if(snprintf(p->root_name,sizeof(p->root_name),"qtt%ldn%" PRIu64, (long)c->pid,qn.origin_ns)>=(int)sizeof(p->root_name)) return qn_error("provision-original-role-root-extent",ENAMETOOLONG); root=qn_provision_directory(parent,p->root_name,0); if(root<0) return -1; prefix=qn_provision_directory(root,"prefix",1); if(prefix<0 || qn_provision_directory(prefix,"query",2)<0) return -1; return 0; } static int qn_provision_directories_check(void) { struct qn_provision *p=&qn.provision; unsigned i; for(i=0;i<3;i++) { struct qn_slot *s; struct stat handle,path; struct qn_version hv,pv; if(!p->root_created[i] || p->root_slots[i]<0 || (unsigned)p->root_slots[i]>=qn.slots_used) return qn_error("provision-original-directory-not-issued",EPROTO); s=&qn.slots[p->root_slots[i]]; if(s->fd<0 || s->close_attempted || s->parent<0 || qn_fstat(s->fd,&handle,"provision-original-directory-release-handle")<0 || qn_fstatat(s->parent,s->component,&path,"provision-original-directory-release-path")<0) return -1; hv=qn_stat_version(&handle); pv=qn_stat_version(&path); if(!qn_identity_equal(&hv,&s->handle_before) || !qn_identity_equal(&pv,&s->path_before) || !qn_identity_equal(&hv,&pv) || !S_ISDIR(handle.st_mode) || !S_ISDIR(path.st_mode) || (handle.st_mode&07777)!=0700 || (path.st_mode&07777)!=0700 ||
        handle.st_uid!=p->selected_uid || path.st_uid!=p->selected_uid || handle.st_gid!=p->selected_gid || path.st_gid!=p->selected_gid) return qn_error("provision-original-directory-release-owner-mode-generation",ESTALE); } return 0; }
/* The anonymous mapping is PRIVATE native prefix bookkeeping within the
 * original fork/gate operation. It is neither a file transport nor a Python
 * object/manifest. Exec removes it from the target. Allocation/reservation
 * precedes fork; actual counters merge exactly once after exec EOF/terminal.
 */ struct qn_prefix_journal { _Atomic unsigned calls,metadata; _Atomic int finished,failed,exec_attempted;
  /* Source-selected actual parent publication; readiness is DATA, never
   * policy permission, a clock, a copied descriptor owner or a new channel. */ _Atomic int root_ready,root_bound; pid_t root_pid; uid_t root_uid; gid_t root_gid; char root_name[65]; struct qn_version root_version;
  /* Child-local acquisition is registered before open and one-close.
   * A returned FD number is raw journal DATA and is never used by parent. */ int root_open_attempted,root_open_result,root_open_errno; int root_fchdir_attempted,root_fchdir_result,root_fchdir_errno; int root_close_attempted,root_close_result,root_close_errno;
  int root_failure_errno;
  /* Separate actual child FD-table attempts. Parent flags remain CLOEXEC;
   * the same open file description remains under its original keeper loan. */
  struct qn_keeper_inherit_observation {
    int registered,slot,fd;
    int flags_before_attempted,flags_before_result,flags_before_errno;
    int access_attempted,access_result,access_errno;
    int handle_attempted,handle_result,handle_errno;
    int filesystem_attempted,filesystem_result,filesystem_errno;
    int type_attempted,type_result,type_errno;
    int clear_attempted,clear_result,clear_errno;
    int flags_after_attempted,flags_after_result,flags_after_errno;
    struct qn_version handle;
    unsigned long filesystem_type;
  } keeper_inherit[3];
  int keeper_parent_attempted; pid_t keeper_parent_result;
  int cloexec_range_attempted,cloexec_range_result,cloexec_range_errno;
};
_Static_assert(sizeof(struct qn_keeper_inherit_observation)==176 && _Alignof(struct qn_keeper_inherit_observation)==8 && sizeof(struct qn_prefix_journal)==776 && _Alignof(struct qn_prefix_journal)==8,
               "Original supported atomic native child prefix layout"); _Static_assert(ATOMIC_INT_LOCK_FREE==2,"Selected native lock-free prefix journal"); static void qn_prefix_attempt(struct qn_prefix_journal *j,int metadata) { atomic_fetch_add_explicit(&j->calls,1U,memory_order_relaxed); if(metadata) atomic_fetch_add_explicit(&j->metadata,1U,memory_order_relaxed); } static void qn_provision_child_error(struct qn_prefix_journal *j,int fd,int error) { const unsigned char *bytes=(const unsigned char *)&error; size_t left=sizeof(error); unsigned attempt=0; if(error<=0) error=EIO; atomic_store_explicit(&j->failed,error,memory_order_release); while(left && attempt++<sizeof(error)) { ssize_t n; qn_prefix_attempt(j,0); n=write(fd,bytes,left); if(n<=0) break; bytes+=(size_t)n; left-=(size_t)n; } qn_prefix_attempt(j,0); atomic_store_explicit(&j->finished,1,memory_order_release); _exit(125); } static int qn_provision_root_publish(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; struct qn_prefix_journal *j=p->prefix_journal; struct qn_slot *s; struct stat handle,path; struct qn_version hv,pv; if(!j || atomic_load_explicit(&j->root_ready,memory_order_acquire) || !c->child_created || c->pid<=0 || !p->prepared || !p->bound || !p->root_created[0] || !p->root_created[1] || !p->root_created[2] || p->root_parent<0 || (unsigned)p->root_parent>=qn.slots_used || qn.slots[p->root_parent].fd<0 || qn.slots[p->root_parent].close_attempted || p->root_slots[0]<0 || (unsigned)p->root_slots[0]>=qn.slots_used || !qn_component(p->root_name)) return qn_error("provision-original-root-data-publication",EPROTO); s=&qn.slots[p->root_slots[0]]; if(s->fd<0 || s->close_attempted || s->parent!=p->root_parent || strcmp(s->component,p->root_name) || qn_fstat(s->fd,&handle,"provision-root-data-held-generation")<0 || qn_fstatat(s->parent,s->component,&path,"provision-root-data-named-generation")<0) return -1; hv=qn_stat_version(&handle); pv=qn_stat_version(&path); if(!qn_identity_equal(&hv,&s->handle_before) ||
      !qn_identity_equal(&pv,&s->path_before) || !qn_version_equal(&hv,&pv) || !S_ISDIR(handle.st_mode) || (handle.st_mode&07777)!=0700 || (path.st_mode&07777)!=0700 || handle.st_uid!=p->selected_uid || path.st_uid!=p->selected_uid || handle.st_gid!=p->selected_gid || path.st_gid!=p->selected_gid) return qn_error("provision-original-root-data-generation",ESTALE);
  /* Prefix/query creation legitimately changed this root's timestamps and
   * nlink. Publish these ACTUAL post-create equal path/handle observations. */ j->root_pid=c->pid; j->root_uid=handle.st_uid; j->root_gid=handle.st_gid; memcpy(j->root_name,p->root_name,strlen(p->root_name)+1); j->root_version=hv; atomic_store_explicit(&j->root_ready,1,memory_order_release); return 0; } static void qn_provision_child_root(struct qn_prefix_journal *j,int exec_writer) { struct qn_provision *p=&qn.provision; struct stat handle,before,cwd,after; struct qn_version hv,bv,cv,av; pid_t actual; char expected[65]; int root=-1,error=0,returned,raw_errno; unsigned root_parent;
  /* This child has only the genuine PREFORK RunnerTemp parent FD. Root FD
   * below is independently opened here after the existing gate; no parent
   * post-fork FD or ordinary copied root_slots[] value is used. */ if(!atomic_load_explicit(&j->root_ready,memory_order_acquire) || p->root_parent<0 || (unsigned)p->root_parent>=qn.slots_used) { error=EPROTO; goto done; } root_parent=(unsigned)p->root_parent; if(qn.slots[root_parent].fd<0 || qn.slots[root_parent].close_attempted || j->root_uid!=p->selected_uid || j->root_gid!=p->selected_gid || !qn_component(j->root_name)) { error=EPROTO; goto done; } qn_prefix_attempt(j,1); actual=getpid(); returned=snprintf(expected,sizeof(expected),"qtt%ldn%" PRIu64,(long)actual,qn.origin_ns); if(actual<=0 || actual!=j->root_pid || returned<0 || returned>=(int)sizeof(expected) || strcmp(expected,j->root_name)) { error=EPROTO; goto done; } j->root_open_attempted=1; qn_prefix_attempt(j,0); errno=0; root=openat(qn.slots[root_parent].fd,j->root_name, O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC); j->root_open_result=root; j->root_open_errno=root<0?errno:0; if(root<0) { error=j->root_open_errno; goto done; } qn_prefix_attempt(j,1); if(fstat(root,&handle)<0) { error=errno; goto done; } qn_prefix_attempt(j,1); if(fstatat(qn.slots[root_parent].fd,j->root_name,&before,AT_SYMLINK_NOFOLLOW)<0) { error=errno; goto done; } hv=qn_stat_version(&handle); bv=qn_stat_version(&before); if(!qn_version_equal(&hv,&j->root_version) || !qn_version_equal(&bv,&hv) || !S_ISDIR(handle.st_mode) || (handle.st_mode&07777)!=0700 || (handle.st_uid!=j->root_uid || handle.st_gid!=j->root_gid) || (before.st_uid!=j->root_uid || before.st_gid!=j->root_gid)) { error=ESTALE; goto done; } j->root_fchdir_attempted=1; qn_prefix_attempt(j,0); errno=0; returned=fchdir(root); raw_errno=returned<0?errno:0; j->root_fchdir_result=returned; j->root_fchdir_errno=raw_errno; if(returned<0) { error=raw_errno; goto done; }
  /* Observe the real kernel cwd plus independent nofollow named root again.
   * Kernel cwd survives exec; this local CLOEXEC FD does not cross loader. */ qn_prefix_attempt(j,1); if(fstatat(AT_FDCWD,".",&cwd,AT_SYMLINK_NOFOLLOW)<0) { error=errno; goto done; } qn_prefix_attempt(j,1); if(fstatat(qn.slots[root_parent].fd,j->root_name,&after,AT_SYMLINK_NOFOLLOW)<0) { error=errno; goto done; } cv=qn_stat_version(&cwd); av=qn_stat_version(&after); if(!qn_version_equal(&cv,&hv) || !qn_version_equal(&av,&hv) || cwd.st_uid!=j->root_uid || cwd.st_gid!=j->root_gid || after.st_uid!=j->root_uid || after.st_gid!=j->root_gid) error=ESTALE; done: if(root>=0) { int owned=root; root=-1; /* one-close ownership retired before syscall */ j->root_close_attempted=1; qn_prefix_attempt(j,0); errno=0; returned=close(owned); raw_errno=returned<0?errno:0; j->root_close_result=returned; j->root_close_errno=raw_errno; if(returned<0 && !error) error=raw_errno;
    /* A negative/unknown close is retained, never retried. Original _exit
     * closes the dying child's remaining table; it issues no success grant. */ } if(error) { if(error<=0) error=EIO; j->root_failure_errno=error; qn_provision_child_error(j,exec_writer,error); } if(!j->root_open_attempted || j->root_open_result<0 || !j->root_fchdir_attempted || j->root_fchdir_result || !j->root_close_attempted || j->root_close_result || j->root_close_errno) qn_provision_child_error(j,exec_writer,EPROTO); atomic_store_explicit(&j->root_bound,1,memory_order_release); } static void qn_provision_child_observations(struct qn_prefix_journal *j,int writer) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  unsigned i; int error=0; pid_t parent;
  if(!l->attempted || !l->prepared || l->retirement_attempted ||
     l->role!=QN_PROVISION || l->source_owner!=(const void *)&qn ||
     l->keeper_pid!=qn.pid || l->origin_ns!=qn.origin_ns ||
     l->cutoff_ns!=qn.cutoff_ns || !l->keeper_start)
    qn_provision_child_error(j,writer,EPROTO);
  /* The actual original fork() gives this child a private descriptor table;
   * this exact CLOEXEC-only operation neither unshares nor closes descriptors.
   * It conveys no ownership of foreign entries and never changes parent flags.
   * Subsequent Source has no open/dup target above2 or descriptor-opening signal
   * continuation before exec; this property remains an admission obligation. */
  if(j->cloexec_range_attempted) qn_provision_child_error(j,writer,EALREADY);
  j->cloexec_range_attempted=1; qn_prefix_attempt(j,0); errno=0;
  j->cloexec_range_result=(int)syscall(SYS_close_range,3U,UINT_MAX,CLOSE_RANGE_CLOEXEC);
  j->cloexec_range_errno=j->cloexec_range_result<0?errno:0;
  if(j->cloexec_range_result!=0)
    qn_provision_child_error(j,writer,j->cloexec_range_result<0?j->cloexec_range_errno:EPROTO);
  j->keeper_parent_attempted=1; qn_prefix_attempt(j,1); parent=getppid();
  j->keeper_parent_result=parent;
  if(parent!=l->keeper_pid) qn_provision_child_error(j,writer,ESRCH);
  for(i=0;i<3;i++) {
    struct qn_keeper_inherit_observation *o=&j->keeper_inherit[i];
    struct qn_slot *s; struct stat st; struct statfs fs; unsigned k;
    int fd,returned;
    o->registered=1; o->slot=l->observation_slots[i]; o->fd=-1;
    if(o->slot<0 || (unsigned)o->slot>=qn.slots_used)
      qn_provision_child_error(j,writer,EPROTO);
    s=&qn.slots[o->slot]; fd=s->fd; o->fd=fd;
    if(!s->registered || s->close_attempted || fd<3)
      qn_provision_child_error(j,writer,EBADF);
    for(k=0;k<i;k++) if(fd==j->keeper_inherit[k].fd)
      qn_provision_child_error(j,writer,EPROTO);
    o->flags_before_attempted=1; qn_prefix_attempt(j,0); errno=0;
    returned=fcntl(fd,F_GETFD); o->flags_before_result=returned;
    o->flags_before_errno=returned<0?errno:0;
    if(returned!=FD_CLOEXEC) { error=returned<0?o->flags_before_errno:EPROTO; goto failed; }
    o->access_attempted=1; qn_prefix_attempt(j,0); errno=0;
    returned=fcntl(fd,F_GETFL); o->access_result=returned;
    o->access_errno=returned<0?errno:0;
    if(returned<0 || (returned&O_ACCMODE)!=O_RDONLY || (returned&O_PATH) ||
       returned!=l->access_flags[i]) {
      error=returned<0?o->access_errno:EPERM; goto failed;
    }
    o->handle_attempted=1; qn_prefix_attempt(j,1); errno=0;
    returned=fstat(fd,&st); o->handle_result=returned; o->handle_errno=returned<0?errno:0;
    if(returned<0) { error=o->handle_errno; goto failed; }
    o->handle=qn_stat_version(&st);
    if(!S_ISREG(st.st_mode) || !qn_identity_equal(&o->handle,&s->handle_before) ||
       st.st_uid!=l->observed_uid[i] || st.st_gid!=l->observed_gid[i]) {
      error=ESTALE; goto failed;
    }
    o->filesystem_attempted=1; qn_prefix_attempt(j,1); errno=0;
    returned=fstatfs(fd,&fs); o->filesystem_result=returned;
    o->filesystem_errno=returned<0?errno:0;
    if(returned<0) { error=o->filesystem_errno; goto failed; }
    o->filesystem_type=(unsigned long)fs.f_type;
    if(o->filesystem_type!=(i<2?(unsigned long)NSFS_MAGIC:(unsigned long)PROC_SUPER_MAGIC)) {
      error=EXDEV; goto failed;
    }
    if(i<2) {
      o->type_attempted=1; qn_prefix_attempt(j,1); errno=0;
      returned=ioctl(fd,NS_GET_NSTYPE,(void *)0); o->type_result=returned;
      o->type_errno=returned<0?errno:0;
      if(returned!=l->namespace_types[i]) {
        error=returned<0?o->type_errno:EXDEV; goto failed;
      }
    }
    /* This is the child's inherited, independently validated owned entry.
     * No foreign descriptor is modified, and the parent's entry is unchanged. */
    o->clear_attempted=1; qn_prefix_attempt(j,0); errno=0;
    returned=fcntl(fd,F_SETFD,o->flags_before_result & ~FD_CLOEXEC); o->clear_result=returned;
    o->clear_errno=returned<0?errno:0;
    if(returned<0) { error=o->clear_errno; goto failed; }
    o->flags_after_attempted=1; qn_prefix_attempt(j,0); errno=0;
    returned=fcntl(fd,F_GETFD); o->flags_after_result=returned;
    o->flags_after_errno=returned<0?errno:0;
    if(returned!=0) { error=returned<0?o->flags_after_errno:EPROTO; goto failed; }
  }
  return;
failed:
  /* No retry, forwarding, positive grant or guessed close of a foreign entry.
   * The original dying-child _exit ends its table; parent retains its debt.
   * Successful exec's receiving owner separately qualifies and owns exact3. */
  qn_provision_child_error(j,writer,error?error:EIO);
}
static void qn_provision_child(void) {
  struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; struct qn_prefix_journal *j=p->prefix_journal; unsigned char token; struct rlimit limit={64,64}; struct sigaction action; char *argv[]={p->image,"-I","-B","-X","utf8",p->script,
    "--linux-preflight-provision","--phase",qn.phase,0}; int signals[]={SIGCHLD,SIGINT,SIGTERM,SIGHUP}; unsigned i; ssize_t n;
#define QN_PREFIX_SYSCALL(EXPR,METADATA) do { \
  qn_prefix_attempt(j,METADATA); \
  if((EXPR)<0) qn_provision_child_error(j,qn.slots[p->exec_writer].fd,errno); \
} while(0)
  QN_PREFIX_SYSCALL(close(qn.slots[p->gate_writer].fd),0); QN_PREFIX_SYSCALL(close(qn.slots[p->exec_reader].fd),0); QN_PREFIX_SYSCALL(close(qn.slots[c->stdout_slot].fd),0); QN_PREFIX_SYSCALL(close(qn.slots[c->stderr_slot].fd),0); QN_PREFIX_SYSCALL(fcntl(qn.slots[p->gate_reader].fd,F_SETFL,0),0); qn_prefix_attempt(j,0); n=read(qn.slots[p->gate_reader].fd,&token,1); if(n<0) qn_provision_child_error(j,qn.slots[p->exec_writer].fd,errno); if(n!=1 || token!=0x51) qn_provision_child_error(j,qn.slots[p->exec_writer].fd,EPROTO); QN_PREFIX_SYSCALL(close(qn.slots[p->gate_reader].fd),0);
  qn_provision_child_root(j,qn.slots[p->exec_writer].fd);
  qn_provision_child_observations(j,qn.slots[p->exec_writer].fd);
  QN_PREFIX_SYSCALL(fcntl(qn.slots[p->out_writer].fd,F_SETFL,0),0); QN_PREFIX_SYSCALL(fcntl(qn.slots[p->err_writer].fd,F_SETFL,0),0); QN_PREFIX_SYSCALL(dup2(qn.slots[p->null_slot].fd,STDIN_FILENO),0); QN_PREFIX_SYSCALL(dup2(qn.slots[p->out_writer].fd,STDOUT_FILENO),0); QN_PREFIX_SYSCALL(dup2(qn.slots[p->err_writer].fd,STDERR_FILENO),0); QN_PREFIX_SYSCALL(setrlimit(RLIMIT_NOFILE,&limit),0); QN_PREFIX_SYSCALL(prctl(PR_SET_KEEPCAPS,0,0,0,0),0); QN_PREFIX_SYSCALL(setgroups(0,0),0); QN_PREFIX_SYSCALL(setgid(p->selected_gid),0); QN_PREFIX_SYSCALL(setuid(p->selected_uid),0); qn_prefix_attempt(j,1); if(geteuid()!=p->selected_uid) qn_provision_child_error(j,qn.slots[p->exec_writer].fd,EPERM); qn_prefix_attempt(j,1); if(getegid()!=p->selected_gid) qn_provision_child_error(j,qn.slots[p->exec_writer].fd,EPERM); memset(&action,0,sizeof(action)); action.sa_handler=SIG_DFL; sigemptyset(&action.sa_mask); for(i=0;i<4;i++) QN_PREFIX_SYSCALL(sigaction(signals[i],&action,0),0); QN_PREFIX_SYSCALL(sigprocmask(SIG_SETMASK,&p->original_mask,0),0); qn_prefix_attempt(j,0); atomic_store_explicit(&j->exec_attempted,1,memory_order_release); atomic_store_explicit(&j->finished,1,memory_order_release); execveat(qn.slots[p->image_slot].fd,"",argv,p->environment,AT_EMPTY_PATH); qn_provision_child_error(j,qn.slots[p->exec_writer].fd,errno);
#undef QN_PREFIX_SYSCALL
} static int qn_provision_prefix_allocation(void) { struct qn_provision *p=&qn.provision; long page; size_t bytes; if(qn_attempt("provision-prefix-native-page",1)<0) return -1; page=sysconf(_SC_PAGESIZE); if(page<=0 || (size_t)page>SIZE_MAX-sizeof(struct qn_prefix_journal)) return qn_error("provision-prefix-native-page",EINVAL); bytes=((sizeof(struct qn_prefix_journal)+(size_t)page-1)/(size_t)page)*(size_t)page;
  /* Exact child maximum: original25 prefix attempts +8 real root binding
   * attempts (getpid/open/fstat/path/fchdir/cwd/path/one-close), plus at most
   * four errno writes and one _exit =38. Original2 getter metadata +5 actual
   * PID/root/cwd metadata =7. Prefix denial or early error never refunds.
   * Whole prebuild Source funding remains the original owner's obligation. */
  /* New exact observations add parent getter1 + namespace7*2 + maps6 + CLOEXEC-range1 =22
   * calls and parent1 + namespace3*2 + maps2 =9 metadata. Failure writes and
   * _exit already belong to the original maximum; no additional allowance. */
  if(bytes>qn.heap_remaining || qn.calls_remaining<60 || qn.metadata_remaining<16)
    return qn_error("provision-prefix-original-allocation",ENOSPC);
  qn.heap_remaining-=bytes; qn.calls_remaining-=60; qn.metadata_remaining-=16;
  p->prefix_bytes=bytes; p->prefix_map_attempted=1; if(qn_attempt("provision-prefix-native-mmap",0)<0) return -1; p->prefix_journal=mmap(0,bytes,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0); if(p->prefix_journal==MAP_FAILED) { p->prefix_journal=0; return qn_error("provision-prefix-native-mmap",errno); } atomic_init(&p->prefix_journal->calls,0); atomic_init(&p->prefix_journal->metadata,0); atomic_init(&p->prefix_journal->finished,0); atomic_init(&p->prefix_journal->failed,0); atomic_init(&p->prefix_journal->exec_attempted,0); atomic_init(&p->prefix_journal->root_ready,0); atomic_init(&p->prefix_journal->root_bound,0); p->prefix_journal->root_pid=0; p->prefix_journal->root_uid=p->prefix_journal->root_gid=0; memset(p->prefix_journal->root_name,0,sizeof(p->prefix_journal->root_name)); memset(&p->prefix_journal->root_version,0,sizeof(p->prefix_journal->root_version)); p->prefix_journal->root_open_attempted=0; p->prefix_journal->root_open_result=-1; p->prefix_journal->root_open_errno=0; p->prefix_journal->root_fchdir_attempted=0; p->prefix_journal->root_fchdir_result=-1; p->prefix_journal->root_fchdir_errno=0; p->prefix_journal->root_close_attempted=0; p->prefix_journal->root_close_result=-1;
  p->prefix_journal->root_close_errno=p->prefix_journal->root_failure_errno=0;
  memset(p->prefix_journal->keeper_inherit,0,sizeof(p->prefix_journal->keeper_inherit));
  p->prefix_journal->keeper_parent_attempted=0;
  p->prefix_journal->keeper_parent_result=0;
  p->prefix_journal->cloexec_range_attempted=0;
  p->prefix_journal->cloexec_range_result=p->prefix_journal->cloexec_range_errno=0;
  return 0; } static int qn_provision_prefix_merge(void) { struct qn_provision *p=&qn.provision; unsigned calls,metadata; if(p->prefix_merged) return 0; if(!p->prefix_journal || !atomic_load_explicit(&p->prefix_journal->finished,memory_order_acquire)) return qn_error("provision-prefix-native-journal-unfinished",EPROTO); calls=atomic_load_explicit(&p->prefix_journal->calls,memory_order_relaxed);
  metadata=atomic_load_explicit(&p->prefix_journal->metadata,memory_order_relaxed);
  if(!calls || calls>60 || metadata>16 || metadata>calls)
    return qn_error("provision-prefix-native-journal-range",EPROTO); if(atomic_load_explicit(&p->prefix_journal->exec_attempted,memory_order_acquire) && (!atomic_load_explicit(&p->prefix_journal->root_ready,memory_order_acquire) || !atomic_load_explicit(&p->prefix_journal->root_bound,memory_order_acquire) || !p->prefix_journal->root_open_attempted || p->prefix_journal->root_open_result<0 || p->prefix_journal->root_open_errno || !p->prefix_journal->root_fchdir_attempted || p->prefix_journal->root_fchdir_result || p->prefix_journal->root_fchdir_errno || !p->prefix_journal->root_close_attempted || p->prefix_journal->root_close_result || p->prefix_journal->root_close_errno || p->prefix_journal->root_failure_errno)) return qn_error("provision-prefix-original-root-not-bound",EPROTO);
  if(atomic_load_explicit(&p->prefix_journal->exec_attempted,memory_order_acquire)) {
    struct qn_keeper_observation_loan *l=&p->keeper_observations; unsigned i;
    if(!l->prepared || !p->prefix_journal->cloexec_range_attempted ||
       p->prefix_journal->cloexec_range_result || p->prefix_journal->cloexec_range_errno ||
       !p->prefix_journal->keeper_parent_attempted ||
       p->prefix_journal->keeper_parent_result!=l->keeper_pid)
      return qn_error("provision-prefix-original-keeper-parent-not-bound",EPROTO);
    for(i=0;i<3;i++) {
      struct qn_keeper_inherit_observation *o=&p->prefix_journal->keeper_inherit[i];
      if(!o->registered || o->slot!=l->observation_slots[i] || o->slot<0 ||
         (unsigned)o->slot>=qn.slots_used || o->fd!=qn.slots[o->slot].fd ||
         !o->flags_before_attempted || o->flags_before_result!=FD_CLOEXEC ||
         o->flags_before_errno || !o->access_attempted || o->access_result<0 ||
         o->access_errno || (o->access_result&O_ACCMODE)!=O_RDONLY ||
         !o->handle_attempted || o->handle_result || o->handle_errno ||
         !qn_identity_equal(&o->handle,&qn.slots[o->slot].handle_before) ||
         !o->filesystem_attempted || o->filesystem_result || o->filesystem_errno ||
         o->filesystem_type!=(i<2?(unsigned long)NSFS_MAGIC:(unsigned long)PROC_SUPER_MAGIC) ||
         (i<2 && (!o->type_attempted || o->type_result!=l->namespace_types[i] || o->type_errno)) ||
         !o->clear_attempted || o->clear_result || o->clear_errno ||
         !o->flags_after_attempted || o->flags_after_result || o->flags_after_errno)
        return qn_error("provision-prefix-original-three-role-inheritance",EPROTO);
    }
  }
  p->prefix_merged=1; qn.syscall_calls+=calls; qn.metadata_calls+=metadata;
  return 0; }  static int qn_provision_null_input(int parent) { struct stat before,handle,after; struct qn_version hv,pv; int slot=qn_slot_register(parent,"null"); if(slot<0) return -1; if(qn_fstatat(parent,"null",&before,"provision-original-null-path-before")<0 || !S_ISCHR(before.st_mode) || before.st_uid || major(before.st_rdev)!=1 || minor(before.st_rdev)!=3) return qn_error("provision-original-selected-null",EINVAL); qn.slots[slot].path_before=qn_stat_version(&before); if(qn_attempt("provision-original-null-open",0)<0) return -1; qn.slots[slot].fd=openat(qn.slots[parent].fd,"null",O_RDONLY|O_NOFOLLOW|O_CLOEXEC); if(qn.slots[slot].fd<0 || qn_fstat(qn.slots[slot].fd,&handle,"provision-original-null-handle")<0 || qn_fstatat(parent,"null",&after,"provision-original-null-path-after")<0) return qn_error("provision-original-null-open",errno); hv=qn_stat_version(&handle); pv=qn_stat_version(&after); if(!qn_version_equal(&qn.slots[slot].path_before,&pv) || !qn_identity_equal(&pv,&hv) || handle.st_rdev!=before.st_rdev ||
      after.st_rdev!=before.st_rdev || handle.st_uid!=before.st_uid) return qn_error("provision-original-null-generation",ESTALE); qn.slots[slot].handle_before=hv; return slot; }  static int qn_provision_scope_show(unsigned index,int release) { char *show[]={"/usr/bin/sudo","-n","--","/usr/bin/systemctl","show","--no-pager","--all",
    "--property=Id,LoadState,Transient,InvocationID,ControlGroup,ActiveState",qn.bootstrap,0}; struct qn_manager_fields fields; char expected[160]; struct qn_provision *p=&qn.provision; struct qn_command *c; if(qn_command_run(index,show,0)<0) return -1; c=&qn.commands[index]; if(!c->registered || c->pending || !c->child_created || !c->exec_proven || !c->terminal || c->status || !c->stdout_eof || !c->stderr_eof || c->stderr_used || !c->stdout_used || c->stdout_used>4096 || !c->stdout_data || strlen(c->stdout_data)!=c->stdout_used || c->stdout_data[c->stdout_used-1]!='\n') return qn_error("provision-original-scope-manager-command-receipt",EPROTO); if(qn_manager_decode(c->stdout_data,&fields)<0 || strcmp(fields.id,qn.bootstrap) || strcmp(fields.load,"loaded") || strcmp(fields.transient,"yes") || strcmp(fields.active,"active") || !qn_hex32(fields.invocation) || snprintf(expected,sizeof(expected),"%s/%s/%s",qn.ancestor_group,qn.common,qn.bootstrap)>=(int)sizeof(expected) || strcmp(fields.group,expected)) return qn_error("provision-original-scope-manager-generation",ESTALE); if(release) { if(strcmp(p->bootstrap_invocation,fields.invocation)) return qn_error("provision-original-scope-manager-replacement",ESTALE); } else memcpy(p->bootstrap_invocation,fields.invocation,sizeof(p->bootstrap_invocation)); return 0; }
/* Use after qn_baseline_create_at and existing qn_command_run are declared.
 * The same qn_owner owns the pending policy journal, command rows and file slots. */ static int qn_policy_literal_path(const char *value) { const unsigned char *p=(const unsigned char *)value,*start; unsigned depth=0; size_t n; if(!p || *p!='/' || !p[1] || strlen(value)>=QN_PATH) return -1; ++p; while(*p) { start=p; while(*p && *p!='/') { if(!((*p>='A'&&*p<='Z') || (*p>='a'&&*p<='z') || (*p>='0'&&*p<='9') || *p=='_' || *p=='.' || *p=='-')) return -1; ++p; } n=(size_t)(p-start); if(!n || n>NAME_MAX || ++depth>64 || (n==1&&start[0]=='.') || (n==2&&start[0]=='.'&&start[1]=='.')) return -1; if(*p=='/' && !*++p) return -1; } return 0; } static int qn_policy_same_original_store(const char *path) { size_t n=strlen(QN_SOURCE_SNAPSHOT_ROOT); return !strncmp(path,QN_SOURCE_SNAPSHOT_ROOT,n) && path[n]=='/' && path[n+1]; } static int qn_policy_selected_input(const char *path) { unsigned i; int slot=-1,baseline=-1,result=-1; unsigned long flags; struct qn_input *p; for(i=0;i<qn.input_count;i++) if(!strcmp(qn.inputs[i].source,path)) break; if(i==qn.input_count) return qn_error("policy-not-original-selected-input",EPERM); p=&qn.inputs[i]; slot=qn_regular_absolute(path); if(slot<0) goto done; baseline=qn_regular_absolute(p->snapshot); if(baseline<0) goto done; if(!qn_version_equal(&qn.slots[slot].path_before,&p->protected_source_path) || !qn_version_equal(&qn.slots[slot].handle_before,&p->protected_source_handle) || !qn_version_equal(&qn.slots[baseline].path_before,&p->protected_baseline_path) || !qn_version_equal(&qn.slots[baseline].handle_before,&p->protected_baseline_handle) || qn_immutable_slot(slot,&flags)<0 || flags!=p->flags || qn_immutable_slot(baseline,&flags)<0 || flags!=p->baseline_flags || qn_compare_slots(slot,baseline,p->length)<0) { qn_error("policy-original-protected-input-and-baseline-generation",ESTALE); goto done; } result=slot; done: if(baseline>=0 && !qn.slots[baseline].close_attempted && qn_close_slot(baseline)<0) result=-1;
  if(result<0 && slot>=0 && !qn.slots[slot].close_attempted && qn_close_slot(slot)<0) result=-1; return result; } static int qn_policy_bytes_check(int slot,const void *expected,size_t extent) { unsigned char chunk[QN_CHUNK],extra; size_t offset=0; ssize_t got; struct qn_version before; if(qn_check_slot(slot,1)<0 || qn_seek_start(slot)<0) return -1; before=qn.slots[slot].handle_before; while(offset<extent) { size_t request=extent-offset; if(request>QN_CHUNK) request=QN_CHUNK; got=qn_read(slot,chunk,request); if(got<=0 || memcmp(chunk,(const unsigned char *)expected+offset,(size_t)got)) return qn_error("policy-complete-independent-byte-readback",EIO); offset+=(size_t)got; } got=qn_read(slot,&extra,1); if(got<0 || got || qn_check_slot(slot,1)<0 || !qn_version_equal(&before,&qn.slots[slot].handle_before)) return qn_error("policy-readback-eof-and-generation",ESTALE); return 0; } static int qn_policy_flag_owner_check(int slot,const struct qn_policy_flag_effect *effect) { struct stat path,handle; if(qn_fstat(qn.slots[slot].fd,&handle,"policy-owned-flag-handle")<0 || qn_fstatat(qn.slots[slot].parent,qn.slots[slot].component,&path,
       "policy-owned-flag-path")<0) return -1; if(handle.st_uid!=effect->uid || path.st_uid!=effect->uid || handle.st_gid!=effect->gid || path.st_gid!=effect->gid) return qn_error("policy-owned-original-flag-owner",ESTALE); return 0; } static int qn_policy_protect(int slot,unsigned long *original,int *attempted, struct qn_policy_flag_effect *effect) { unsigned long wanted,current; struct stat path,handle; if(*attempted) return qn_error("policy-original-protection-single-use",EALREADY); *attempted=1; if(qn_check_slot(slot,1)<0 || qn_current_flags(slot,original)<0 || qn_fstat(qn.slots[slot].fd,&handle,"policy-owned-flag-handle")<0 || qn_fstatat(qn.slots[slot].parent,qn.slots[slot].component,&path,
       "policy-owned-flag-path")<0) return -1; effect->uid=handle.st_uid; effect->gid=handle.st_gid; effect->before_path=qn.slots[slot].path_before; effect->before_handle=qn.slots[slot].handle_before; { struct qn_version pv=qn_stat_version(&path),hv=qn_stat_version(&handle); if(path.st_uid!=handle.st_uid || path.st_gid!=handle.st_gid || handle.st_uid!=geteuid() || !qn_version_equal(&pv,&effect->before_path) || !qn_version_equal(&hv,&effect->before_handle)) return qn_error("policy-original-flag-before-owner-and-generation",ESTALE); } wanted=*original|FS_IMMUTABLE_FL; if(wanted!=*original) { if(qn_attempt("policy-original-immutable-set",0)<0) return -1; effect->attempted=1; if(ioctl(qn.slots[slot].fd,FS_IOC_SETFLAGS,&wanted)<0) { effect->native_errno=errno; return qn_error("policy-original-immutable-set",effect->native_errno); } effect->returned=1; /* Actual returned mutation, BEFORE follow-up readback. */ if(qn_refresh_after_flag_effect(slot,wanted)<0 || qn_policy_flag_owner_check(slot,effect)<0) return -1; } if(qn_immutable_slot(slot,&current)<0) return -1; if(current!=wanted) return qn_error("policy-exact-original-protected-flags",ESTALE); effect->generation_retained=1; return 0; } static int qn_policy_label_check(pid_t pid) { char number[32],expected[160],actual[256]; size_t n; int proc=-1,attr=-1,result=-1; if(pid!=qn.pid && pid!=qn.commands[8].pid) return qn_error("policy-fixed-actor",EPERM); if(snprintf(number,sizeof(number),"%ld",(long)pid)>=(int)sizeof(number) || snprintf(expected,sizeof(expected),"%scontroller (enforce)\n",qn.stem)>=(int)sizeof(expected)) return qn_error("policy-fixed-actor-label-extent",ENAMETOOLONG); proc=qn_open_component(qn.proc_slot,number,1,0); if(proc<0) return -1; attr=qn_open_component(proc,"attr",1,0); if(attr<0) goto done; if(qn_read_component_text(attr,"current",actual,sizeof(actual),&n)<0 || n!=strlen(expected) || memcmp(actual,expected,n)) { qn_error("policy-same-original-enforced-actor-label",EPERM); goto done; } result=0; done:
  if(attr>=0 && !qn.slots[attr].close_attempted && qn_close_slot(attr)<0) result=-1; if(proc>=0 && !qn.slots[proc].close_attempted && qn_close_slot(proc)<0) result=-1; return result; } /* Same held original /proc/<keeper> directory supplies every start/stat,
 * namespace and maps association. Namespace magic links are the only precise
 * nofollow exception; neither their spelling nor this journal is authority. */
static int qn_keeper_start_from_held(struct qn_keeper_check *o) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  char decimal[32],text[4096],*close,*p,*end; size_t n,pid_bytes; unsigned field;
  if(o->registered) return qn_error("keeper-original-start-occurrence-single-use",EALREADY);
  memset(o,0,sizeof(*o));o->registered=1;
  if(l->keeper_pid!=qn.pid || l->process_slot<0 || l->stat_slot<0 ||
     (unsigned)l->process_slot>=qn.slots_used || (unsigned)l->stat_slot>=qn.slots_used ||
     qn.slots[l->stat_slot].parent!=l->process_slot ||
     qn_check_slot(l->process_slot,0)<0 ||
     qn_read_text(l->stat_slot,text,sizeof(text),&n)<0) return -1;
  if(snprintf(decimal,sizeof(decimal),"%ld",(long)l->keeper_pid)>=(int)sizeof(decimal))
    return qn_error("keeper-original-start-pid-extent",EINVAL);
  pid_bytes=strlen(decimal);
  if(n<=pid_bytes+4 || memcmp(text,decimal,pid_bytes) ||
     text[pid_bytes]!=' ' || text[pid_bytes+1]!='(')
    return qn_error("keeper-original-start-pid-association",EPROTO);
  close=strrchr(text,')');
  if(!close || close[1]!=' ' || !close[2] || close[3]!=' ' ||
     close[2]=='Z' || close[2]=='X')
    return qn_error("keeper-original-start-live-shape",EPROTO);
  p=close+4;
  for(field=4;field<22;field++) {
    end=strchr(p,' '); if(!end || end==p)
      return qn_error("keeper-original-start-stat-field",EPROTO);
    p=end+1;
  }
  end=strchr(p,' ');
  if(!end || end==p || (size_t)(end-p)>=32)
    return qn_error("keeper-original-start-stat-start-field",EPROTO);
  *end=0;
  if(qn_decimal(p,UINT64_MAX,&o->start_ticks)<0 || !o->start_ticks)
    return qn_error("keeper-original-start-value",EPROTO);
  o->stat_returned=1; return 0;
}
static int qn_keeper_original_check(unsigned occurrence) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  struct qn_keeper_check *o; struct pollfd port;
  if(occurrence>=4 || !l->attempted || l->role!=QN_PROVISION ||
     l->source_owner!=(const void *)&qn || l->keeper_pid!=qn.pid ||
     l->origin_ns!=qn.origin_ns || l->cutoff_ns!=qn.cutoff_ns ||
     l->source_input_count!=qn.input_count ||
     l->source_catalogue_count!=qn.catalogue_count ||
     l->source_alias_count!=qn.alias_count || l->keeper_pid_slot<0 ||
     (unsigned)l->keeper_pid_slot>=qn.slots_used ||
     qn.slots[l->keeper_pid_slot].fd<0 || qn.slots[l->keeper_pid_slot].close_attempted)
    return qn_error("keeper-original-source-lifetime",EPROTO);
  o=&l->keeper_checks[occurrence];
  if(qn_keeper_start_from_held(o)<0) return -1;
  if(o->start_ticks!=l->keeper_start) return qn_error("keeper-original-start-changed",ESTALE);
  port=(struct pollfd){qn.slots[l->keeper_pid_slot].fd,POLLIN,0};
  if(qn_attempt("keeper-original-pidfd-live-observation",0)<0) return -1;
  o->poll_attempted=1;errno=0;o->poll_result=poll(&port,1,0);
  o->poll_errno=o->poll_result<0?errno:0;o->poll_revents=port.revents;
  if(o->poll_result!=0 || o->poll_revents)
    return qn_error("keeper-original-pidfd-live-observation",o->poll_result<0?o->poll_errno:ESRCH);
  /* pidfd observes original life; it neither keeps mm alive nor excludes exec.
   * The SAME synchronous original Bash continuation supplies noexec lifetime. */
  return 0;
}
static int qn_keeper_namespace_link(unsigned role,const struct stat *handle) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  const char *name=role==0?"cgroup":"mnt"; char text[64],expected[64]; ssize_t n; int made;
  if(role>=2 || l->namespace_slot<0 || 63U>qn.read_remaining ||
     qn_attempt("keeper-original-namespace-readlink",0)<0) return -1;
  n=readlinkat(qn.slots[l->namespace_slot].fd,name,text,sizeof(text)-1);
  if(n<0) return qn_error("keeper-original-namespace-readlink",errno);
  qn.read_remaining-=(uint64_t)n;qn.read_bytes+=(uint64_t)n;
  if(qn.largest_read<sizeof(text)-1) qn.largest_read=sizeof(text)-1;
  made=snprintf(expected,sizeof(expected),"%s:[%" PRIuMAX "]",name,(uintmax_t)handle->st_ino);
  if(made<=0 || made>=(int)sizeof(expected) || n!=made || memchr(text,0,(size_t)n) ||
     memcmp(text,expected,(size_t)n))
    return qn_error("keeper-original-namespace-link-and-object",ESTALE);
  return 0;
}
static int qn_keeper_observation_check(unsigned role,int initial) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  struct qn_slot *s; struct stat st,path; struct statfs fs; struct qn_version hv,pv;
  int number,flags,access,type; const char *name=role==0?"cgroup":role==1?"mnt":"maps";
  if(role>=3 || (number=l->observation_slots[role])<0 || (unsigned)number>=qn.slots_used)
    return qn_error("keeper-original-role-slot",EINVAL);
  s=&qn.slots[number];
  if(!s->registered || s->fd<3 || s->close_attempted ||
     s->parent!=(role<2?l->namespace_slot:l->process_slot) || strcmp(s->component,name) ||
     qn_fstat(s->fd,&st,"keeper-original-role-held")<0 ||
     qn_fstatat(s->parent,name,&path,"keeper-original-role-path")<0) return -1;
  hv=qn_stat_version(&st);pv=qn_stat_version(&path);
  if(!S_ISREG(st.st_mode) || !qn_identity_equal(&hv,&s->handle_before) ||
     st.st_uid!=l->observed_uid[role] || st.st_gid!=l->observed_gid[role])
    return qn_error("keeper-original-role-held-generation",ESTALE);
  if(role<2) {
    if(!S_ISLNK(path.st_mode) || !qn_version_equal(&pv,&l->namespace_links[role]))
      return qn_error("keeper-original-namespace-link-generation",ESTALE);
  } else if(!qn_identity_equal(&pv,&hv) || path.st_uid!=l->observed_uid[role] ||
            path.st_gid!=l->observed_gid[role])
    return qn_error("keeper-original-maps-path-and-holder",ESTALE);
  if(qn_attempt("keeper-original-role-filesystem",1)<0 ||
     fstatfs(s->fd,&fs)<0) return qn_error("keeper-original-role-filesystem",errno);
  if((unsigned long)fs.f_type!=(role<2?(unsigned long)NSFS_MAGIC:(unsigned long)PROC_SUPER_MAGIC))
    return qn_error("keeper-original-role-kernel-kind",EXDEV);
  if(qn_attempt("keeper-original-role-getfd",0)<0) return -1;
  flags=fcntl(s->fd,F_GETFD);
  if(flags!=FD_CLOEXEC) return qn_error("keeper-original-role-parent-noninherited",flags<0?errno:EPROTO);
  if(qn_attempt("keeper-original-role-getfl",0)<0) return -1;
  access=fcntl(s->fd,F_GETFL);
  if(access<0 || (access&O_ACCMODE)!=O_RDONLY || (access&O_PATH) ||
     (!initial && access!=l->access_flags[role]))
    return qn_error("keeper-original-role-readonly",access<0?errno:EPERM);
  if(initial) { l->descriptor_flags[role]=flags;l->access_flags[role]=access; }
  if(role<2) {
    if(qn_attempt("keeper-original-namespace-type",1)<0) return -1;
    type=ioctl(s->fd,NS_GET_NSTYPE,(void *)0);
    if(type!=(role==0?CLONE_NEWCGROUP:CLONE_NEWNS))
      return qn_error("keeper-original-namespace-type",type<0?errno:EXDEV);
    if(initial) l->namespace_types[role]=type;
    if(type!=l->namespace_types[role] || qn_keeper_namespace_link(role,&st)<0) return -1;
  } else if(initial) {
    off_t offset;
    if(qn_attempt("keeper-original-maps-unread-cursor",0)<0) return -1;
    offset=lseek(s->fd,0,SEEK_CUR);
    if(offset!=0) return qn_error("keeper-original-maps-unread-cursor",offset<0?errno:EPROTO);
    l->maps_initial_offset=offset;
  }
  return 0;
}
static int qn_keeper_namespace_open(unsigned role) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  const char *name=role==0?"cgroup":"mnt"; struct stat before,st; struct qn_slot *s; int number;
  if(role>=2) return qn_error("keeper-original-namespace-fixed-role",EINVAL);
  number=qn_slot_register(l->namespace_slot,name);l->observation_slots[role]=number;
  if(number<0) return -1;
  s=&qn.slots[number];
  if(qn_fstatat(l->namespace_slot,name,&before,"keeper-original-namespace-link-before")<0 ||
     !S_ISLNK(before.st_mode)) return qn_error("keeper-original-namespace-magic-kind",EINVAL);
  s->path_before=qn_stat_version(&before);l->namespace_links[role]=s->path_before;
  if(qn_attempt("keeper-original-fixed-namespace-open",0)<0) return -1;
  /* Follow ONLY this exact proc/ns magic link beneath the actual held keeper.
   * O_NOFOLLOW is retained for every ordinary directory, stat and maps input. */
  s->fd=openat(qn.slots[l->namespace_slot].fd,name,O_RDONLY|O_CLOEXEC);
  if(s->fd<0) return qn_error("keeper-original-fixed-namespace-open",errno);
  if(qn_fstat(s->fd,&st,"keeper-original-namespace-first-handle")<0) return -1;
  s->handle_before=qn_stat_version(&st);l->observed_uid[role]=st.st_uid;l->observed_gid[role]=st.st_gid;
  return qn_keeper_observation_check(role,1);
}
static int qn_keeper_observation_slots_close(void) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  int slots[7]={l->observation_slots[2],l->observation_slots[1],l->observation_slots[0],
    l->namespace_slot,l->stat_slot,l->process_slot,l->keeper_pid_slot};
  unsigned i;int result=0;
  for(i=0;i<7;i++) if(slots[i]>=0 && (unsigned)slots[i]<qn.slots_used) {
    struct qn_slot *s=&qn.slots[slots[i]];
    if(!s->close_attempted) { if(qn_close_slot(slots[i])<0) result=-1; }
    else if(s->close_result<0 || s->close_errno) result=-1;
  }
  return result;
}
static int qn_keeper_observations_prepare(void) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  char decimal[32];struct stat st;unsigned i;
  if(l->attempted) return qn_error("keeper-original-observations-single-use",EALREADY);
  l->attempted=1;l->role=QN_PROVISION;l->keeper_pid=qn.pid;
  l->source_owner=(const void *)&qn;l->origin_ns=qn.origin_ns;l->cutoff_ns=qn.cutoff_ns;
  l->source_input_count=qn.input_count;l->source_catalogue_count=qn.catalogue_count;
  l->source_alias_count=qn.alias_count;
  if(qn.stage!=QN_PREPARING || !qn.provision.mask_held || !qn.catalogue_complete ||
     snprintf(decimal,sizeof(decimal),"%ld",(long)qn.pid)>=(int)sizeof(decimal)) {
    qn_error("keeper-original-prefork-origin-and-source",EPROTO);goto failed;
  }
  l->process_slot=qn_open_component(qn.proc_slot,decimal,1,0);
  if(l->process_slot<0) goto failed;
  l->stat_slot=qn_open_component(l->process_slot,"stat",0,0);
  if(l->stat_slot<0 || qn_keeper_start_from_held(&l->keeper_checks[0])<0) goto failed;
  l->keeper_start=l->keeper_checks[0].start_ticks;
  l->keeper_pid_slot=qn_pidfd_slot(qn.pid);
  l->namespace_slot=qn_open_component(l->process_slot,"ns",1,0);
  if(l->keeper_pid_slot<0 || l->namespace_slot<0) goto failed;
  for(i=0;i<2;i++) if(qn_keeper_namespace_open(i)<0) goto failed;
  l->observation_slots[2]=qn_open_component(l->process_slot,"maps",0,0);
  if(l->observation_slots[2]<0 ||
     qn_fstat(qn.slots[l->observation_slots[2]].fd,&st,"keeper-original-maps-first-handle")<0)
    goto failed;
  l->observed_uid[2]=st.st_uid;l->observed_gid[2]=st.st_gid;
  if(qn_keeper_observation_check(2,1)<0) goto failed;
  return 0;
failed:
  l->partial_close_attempted=1;l->partial_close_result=qn_keeper_observation_slots_close();
  return -1;
}
static int qn_keeper_observations_prefork_join(void) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;unsigned i;
  if(!l->attempted || l->prepared || l->partial_close_attempted ||
     qn_keeper_original_check(1)<0) return -1;
  for(i=0;i<3;i++) if(qn_keeper_observation_check(i,0)<0) return -1;
  l->prepared=1;return 0;
}
static int qn_keeper_observations_release_join(void) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;unsigned i;off_t offset;
  if(!l->prepared || l->retirement_attempted ||
     qn_keeper_original_check(2)<0) return -1;
  for(i=0;i<3;i++) if(qn_keeper_observation_check(i,0)<0) return -1;
  if(qn_attempt("keeper-original-maps-release-unread-cursor",0)<0) return -1;
  offset=lseek(qn.slots[l->observation_slots[2]].fd,0,SEEK_CUR);
  if(offset!=l->maps_initial_offset || offset!=0)
    return qn_error("keeper-original-maps-release-unread-cursor",offset<0?errno:EPROTO);
  /* No C read or seek changes this maps open-file position. The child is its
   * only reader; the root never competes during original synchronous use. */
  return 0;
}
static int qn_keeper_observations_retire(void) {
  struct qn_keeper_observation_loan *l=&qn.provision.keeper_observations;
  struct qn_provision *p=&qn.provision;struct qn_command *c=&qn.commands[8];unsigned i;int result=0;
  if(l->retirement_attempted) return qn_error("keeper-original-observation-retirement-single-use",EALREADY);
  l->retirement_attempted=1;
  if(!l->prepared || !p->reaped || c->pending || !c->terminal || !c->exec_proven ||
     !c->stdout_eof || !c->stderr_eof || !p->prefix_merged)
    return qn_error("keeper-original-observation-live-retirement-debt",EBUSY);
  if(qn_keeper_original_check(3)<0) result=-1;
  if(!result) for(i=0;i<3;i++) if(qn_keeper_observation_check(i,0)<0) { result=-1;break; }
  /* The genuine child has already been reaped. Aggregate ONLY this keeper's
   * known originated entries even if a rejoin or a close retains an error. */
  if(qn_keeper_observation_slots_close()<0) result=-1;
  if(result<0) return -1;
  l->retired=1;return 0;
}
static int qn_policy_partial_cleanup(void);
static int qn_policy_extend_provision(void) { struct qn_policy_transition *j=&qn.controller_policy; struct qn_command *child=&qn.commands[8],*compiled; const char *temporary=qn_provision_environment_value("RUNNER_TEMP"); char profile[160],config[QN_PATH+32],features[QN_PATH+32],kernel[QN_PATH+32]; char expected[192],extra[QN_PATH*2+64]; int base=-1,conf=-1,feat=-1,result=-1; size_t base_bytes,extra_bytes,total; ssize_t got; unsigned char suffix; char *compile_argv[]={"/usr/bin/sudo","-n","--",QN_SOURCE_APPARMOR_PARSER,config,
    "--skip-cache","--jobs=0","--Werror",features,kernel,"--stdout",j->source,0}; char *replace_argv[]={"/usr/bin/sudo","-n","--",QN_SOURCE_APPARMOR_PARSER,config,
    "--skip-cache","--jobs=0","--binary","--replace",j->binary,0}; if(j->attempted) return qn_error("policy-provision-transition-single-use",EALREADY); memset(j,0,sizeof(*j)); j->attempted=1; j->source_slot=j->binary_slot=j->output_root_slot=-1; /* Before first fallibility. */ j->slots_begin=qn.slots_used; if(qn.stage!=QN_PREPARING || !child->child_created || child->pid<=0 || child->pid_slot<0 || child->start_ticks==0) { qn_error("policy-original-gated-child-record",EPROTO); goto done; } if(qn_complete_startup_check()<0) goto done; if(qn_policy_literal_path(temporary)<0 || qn_policy_literal_path(QN_SOURCE_SNAPSHOT_ROOT)<0 || qn_policy_literal_path(QN_SOURCE_POLICY_BASE)<0 || qn_policy_literal_path(QN_SOURCE_POLICY_CONFIG)<0 || qn_policy_literal_path(QN_SOURCE_POLICY_FEATURES)<0 || qn_policy_literal_path(QN_SOURCE_POLICY_OUTPUT_ROOT)<0 || qn_policy_literal_path(QN_SOURCE_APPARMOR_PARSER)<0 || !qn_policy_same_original_store(QN_SOURCE_POLICY_BASE) || !qn_policy_same_original_store(QN_SOURCE_POLICY_CONFIG) || !qn_policy_same_original_store(QN_SOURCE_POLICY_FEATURES) || !qn_policy_same_original_store(QN_SOURCE_POLICY_OUTPUT_ROOT)) { qn_error("policy-fixed-literal-original-source-path",EINVAL); goto done; } if(qn_policy_label_check(qn.pid)<0 || qn_policy_label_check(child->pid)<0) goto done;
  /* PID is the registered real child, never predicted. No root exists yet. */ if(snprintf(j->root,sizeof(j->root),"%s/qtt%ldn%" PRIu64, temporary,(long)child->pid,qn.origin_ns)>=(int)sizeof(j->root) || qn_policy_literal_path(j->root)<0) { qn_error("policy-real-child-root-literal-extent",EINVAL); goto done; } base=qn_policy_selected_input(QN_SOURCE_POLICY_BASE); conf=qn_policy_selected_input(QN_SOURCE_POLICY_CONFIG); feat=qn_policy_selected_input(QN_SOURCE_POLICY_FEATURES); if(base<0 || conf<0 || feat<0) goto done; if(qn.slots[conf].handle_before.size!=0) { qn_error("policy-original-empty-config-extent",EPROTO); goto done; } if(qn.slots[base].handle_before.size<3 || (uint64_t)qn.slots[base].handle_before.size>=QN_DATA) { qn_error("policy-original-base-profile-extent",ENOSPC); goto done; } base_bytes=(size_t)qn.slots[base].handle_before.size; if(snprintf(profile,sizeof(profile),"%scontroller",qn.stem)>=(int)sizeof(profile) || snprintf(expected,sizeof(expected),"profile %s flags=(attach_disconnected,mediate_deleted) {\n", profile)>=(int)sizeof(expected) || snprintf(config,sizeof(config),"--config-file=%s",QN_SOURCE_POLICY_CONFIG)>=(int)sizeof(config) || snprintf(features,sizeof(features),"--override-policy-abi=%s",QN_SOURCE_POLICY_FEATURES)>=(int)sizeof(features) || snprintf(kernel,sizeof(kernel),"--kernel-features=%s",QN_SOURCE_POLICY_FEATURES)>=(int)sizeof(kernel)) { qn_error("policy-fixed-parser-operand-extent",ENAMETOOLONG); goto done; } extra_bytes=(size_t)snprintf(extra,sizeof(extra),
    "  \"%s\" rw,\n  \"%s/**\" rwk,\n",j->root,j->root); if(extra_bytes>=sizeof(extra) || base_bytes>SIZE_MAX-extra_bytes-1 || (total=base_bytes+extra_bytes)>=QN_DATA || total+1>qn.heap_remaining) { qn_error("policy-prospective-complete-source-storage",ENOSPC); goto done; } qn.heap_remaining-=total+1; j->body=malloc(total+1); if(!j->body) { qn_error("policy-prospective-complete-source-allocation",ENOMEM); goto done; } j->body_bytes=total; if(qn_seek_start(base)<0) goto done; { size_t used=0; while(used<base_bytes) { size_t ask=base_bytes-used; if(ask>QN_CHUNK) ask=QN_CHUNK; got=qn_read(base,j->body+used,ask); if(got<0) goto done; if(!got) { qn_error("policy-original-base-premature-eof",EIO); goto done; } used+=(size_t)got; } } got=qn_read(base,&suffix,1); if(got<0 || got || qn_check_slot(base,1)<0 || base_bytes<strlen(expected) || memcmp(j->body,expected,strlen(expected)) || memchr(j->body,0,base_bytes) || memcmp(j->body+base_bytes-3,"}\n\n",3)) { qn_error("policy-exact-original-base-profile-source",EPROTO); goto done; }
  /* Preserve EVERY base byte, rule and peer. Only insert the two original
   * exact write rules for the real PROVISION root before the final brace. */ memmove(j->body+base_bytes-3+extra_bytes,j->body+base_bytes-3,3); memcpy(j->body+base_bytes-3,extra,extra_bytes); j->body[total]=0; j->output_root_slot=qn_safe_root(QN_SOURCE_POLICY_OUTPUT_ROOT); if(j->output_root_slot<0) goto done; j->source_slot=qn_baseline_create_at(j->output_root_slot,QN_SOURCE_POLICY_OUTPUT_ROOT,
    "controller-provision.profile",-1,j->body,total,j->source); if(j->source_slot<0 || qn_policy_bytes_check(j->source_slot,j->body,total)<0 || qn_policy_protect(j->source_slot,&j->source_original_flags,&j->source_protect_attempted, &j->source_flag_effect)<0 || qn_command_run(QN_POLICY_COMPILE,compile_argv,0)<0) goto done; compiled=&qn.commands[QN_POLICY_COMPILE]; if(!compiled->stdout_used || compiled->stdout_used>QN_POLICY_BINARY_LIMIT || compiled->stderr_used) { qn_error("policy-fixed-existing-64KiB-binary-profile-denial",EFBIG); goto done; } j->compiled=1; j->binary_slot=qn_baseline_create_at(j->output_root_slot,QN_SOURCE_POLICY_OUTPUT_ROOT,
    "controller-provision.binary",-1,compiled->stdout_data,compiled->stdout_used,j->binary); if(j->binary_slot<0 || qn_policy_bytes_check(j->binary_slot,compiled->stdout_data,compiled->stdout_used)<0 || qn_policy_protect(j->binary_slot,&j->binary_original_flags,&j->binary_protect_attempted, &j->binary_flag_effect)<0 || qn_complete_startup_check()<0 || qn_policy_label_check(qn.pid)<0) goto done; j->replace_attempted=1; if(qn_command_run(QN_POLICY_REPLACE,replace_argv,0)<0) goto done; if(qn.commands[QN_POLICY_REPLACE].stdout_used || qn.commands[QN_POLICY_REPLACE].stderr_used) { qn_error("policy-original-replace-empty-output",EPROTO); goto done; } if(qn_policy_label_check(qn.pid)<0 || qn_policy_label_check(child->pid)<0 || qn_policy_bytes_check(j->source_slot,j->body,j->body_bytes)<0 || qn_policy_bytes_check(j->binary_slot,compiled->stdout_data,compiled->stdout_used)<0 || qn_check_slot(base,1)<0 || qn_check_slot(conf,1)<0 || qn_check_slot(feat,1)<0) goto done; j->replaced=1; result=0; done: if(feat>=0 && !qn.slots[feat].close_attempted && qn_close_slot(feat)<0) result=-1; if(conf>=0 && !qn.slots[conf].close_attempted && qn_close_slot(conf)<0) result=-1; if(base>=0 && !qn.slots[base].close_attempted && qn_close_slot(base)<0) result=-1; if(result<0) qn_policy_partial_cleanup(); /* Original error/status stays negative. */ return result; } static int qn_policy_provision_release_check(void) { struct qn_policy_transition *j=&qn.controller_policy; struct qn_command *a=&qn.commands[QN_POLICY_COMPILE],*b=&qn.commands[QN_POLICY_REPLACE]; unsigned long flags; if(!j->attempted || !j->compiled || !j->replace_attempted || !j->replaced || !a->registered || !a->child_created || a->pending || !a->terminal || !a->exec_proven || a->status || !a->stdout_eof || !a->stderr_eof || !a->stdout_used || a->stdout_used>QN_POLICY_BINARY_LIMIT || a->stderr_used || !b->registered || !b->child_created || b->pending || !b->terminal || !b->exec_proven || b->status || !b->stdout_eof || !b->stderr_eof || b->stdout_used || b->stderr_used ||
     qn_policy_bytes_check(j->source_slot,j->body,j->body_bytes)<0 || qn_policy_bytes_check(j->binary_slot,a->stdout_data,a->stdout_used)<0 || qn_immutable_slot(j->source_slot,&flags)<0 || flags!=(j->source_original_flags|FS_IMMUTABLE_FL) || qn_immutable_slot(j->binary_slot,&flags)<0 || flags!=(j->binary_original_flags|FS_IMMUTABLE_FL) || qn_policy_label_check(qn.pid)<0 || qn_policy_label_check(qn.commands[8].pid)<0) return qn_error("policy-real-transition-before-one-shot-release",EPERM); j->checked=1; return 0; }
/* Terminal file debts belong to the same original owner. No policy removal is
 * performed while that controller still lives. Original pre-build owner unloads
 * its actual loaded profile only after genuine controller/descendant death. */ static int qn_policy_restore_original_flags(int slot,unsigned long original,int *attempted) { unsigned long current,wanted=original|FS_IMMUTABLE_FL; if(*attempted) return qn_error("policy-original-flag-restoration-single-use",EALREADY); *attempted=1; /* Publish the terminal attempt before the first fallible getter. */ if(qn_check_slot(slot,1)<0 || qn_current_flags(slot,&current)<0) return -1; if(current!=original && current!=wanted) return qn_error("policy-original-flag-transition-debt",ESTALE); if(current!=original) { if(qn_attempt("policy-original-immutable-restore",0)<0) return -1; if(ioctl(qn.slots[slot].fd,FS_IOC_SETFLAGS,&original)<0) return qn_error("policy-original-immutable-restore",errno); if(qn_refresh_after_flag_effect(slot,original)<0) return -1; } if(qn_current_flags(slot,&current)<0 || current!=original) return qn_error("policy-original-flags-terminal-readback",ESTALE); return 0; }
/* Only local policy prefix resources: original gated PROVISION/root/profile
 * custody remains HELD. Never dispatch, release, reset deadline or reset grants. */ static int qn_policy_parser_quiescent(const struct qn_command *c,int require_nonexec) { int raw_error=0; if(!c->registered) return !c->child_created && !c->pending; if(!c->child_created) return !c->pending && !c->exec_proven && c->pid<=0; if(c->pending || !c->terminal || !c->stdout_eof || !c->stderr_eof || !c->terminal_observation.native_attempted || c->terminal_observation.result || c->terminal_observation.info.si_pid!=c->pid || c->terminal_observation.info.si_code!=CLD_EXITED || c->terminal_observation.info.si_status!=c->status) return 0; if(!require_nonexec) return 1;
  /* False exec_proven alone is not proof. Retain actual complete raw errno,
   * EOF, exact preexec exit and existing real one-reap/pending=false prefix. */ if(c->exec_proven || !c->exec_eof || c->exec_failure_bytes!=sizeof(int) || c->exec_failure_errno<=0 || c->status!=125) return 0; memcpy(&raw_error,c->exec_failure_raw,sizeof(raw_error)); return raw_error==c->exec_failure_errno; } static int qn_policy_partial_version(const struct qn_version *actual, const struct qn_version *before) { return qn_identity_equal(actual,before) && actual->mode==before->mode && actual->links==before->links && actual->size==before->size && actual->mtime.tv_sec==before->mtime.tv_sec && actual->mtime.tv_nsec==before->mtime.tv_nsec; } static int qn_policy_rejoin_returned_flag(int slot,unsigned long original, struct qn_policy_flag_effect *effect,const void *bytes,size_t extent) { struct stat hp,pp,ha,pa; struct qn_version hv,pv,hav,pav; unsigned long flags; unsigned char chunk[QN_CHUNK],extra; size_t offset=0; ssize_t got; if(!effect->attempted || !effect->returned || effect->generation_retained || slot<0 || (unsigned)slot>=qn.slots_used || qn.slots[slot].fd<0) return qn_error("policy-partial-unproved-flag-mutation",EPERM); if(qn_fstat(qn.slots[slot].fd,&hp,"policy-partial-flag-handle")<0 || qn_fstatat(qn.slots[slot].parent,qn.slots[slot].component,&pp,
       "policy-partial-flag-path")<0 || qn_current_flags(slot,&flags)<0) return -1; hv=qn_stat_version(&hp); pv=qn_stat_version(&pp); if(!qn_policy_partial_version(&hv,&effect->before_handle) || !qn_policy_partial_version(&pv,&effect->before_path) || !qn_version_equal(&hv,&pv) || hp.st_uid!=effect->uid || pp.st_uid!=effect->uid || hp.st_gid!=effect->gid || pp.st_gid!=effect->gid || flags!=(original|FS_IMMUTABLE_FL) || hv.size<0 || (uint64_t)hv.size!=extent) return qn_error("policy-partial-returned-flag-only-generation",ESTALE); if(qn_seek_start(slot)<0) return -1; while(offset<extent) { size_t request=extent-offset; if(request>QN_CHUNK) request=QN_CHUNK; got=qn_read(slot,chunk,request); if(got<0) return -1; if(!got || memcmp(chunk,(const unsigned char *)bytes+offset,(size_t)got)) return qn_error("policy-partial-returned-flag-complete-bytes",EIO); offset+=(size_t)got; } got=qn_read(slot,&extra,1); if(got<0) return -1; if(got) return qn_error("policy-partial-returned-flag-suffix",EFBIG); if(qn_fstat(qn.slots[slot].fd,&ha,"policy-partial-flag-handle-after")<0 || qn_fstatat(qn.slots[slot].parent,qn.slots[slot].component,&pa,
       "policy-partial-flag-path-after")<0 || qn_current_flags(slot,&flags)<0) return -1; hav=qn_stat_version(&ha); pav=qn_stat_version(&pa); if(!qn_version_equal(&hv,&hav) || !qn_version_equal(&pv,&pav) || ha.st_uid!=effect->uid || pa.st_uid!=effect->uid || ha.st_gid!=effect->gid || pa.st_gid!=effect->gid || flags!=(original|FS_IMMUTABLE_FL)) return qn_error("policy-partial-returned-flag-stable-full-readback",ESTALE);
  /* Rejoin only after actual returned mutation AND complete independent bytes
   * and every other original property, never a generic immediate-stat grant. */ qn.slots[slot].path_before=pav; qn.slots[slot].handle_before=hav; effect->generation_retained=1; return 0; } static int qn_policy_partial_file_restore(int slot,unsigned long original, struct qn_policy_flag_effect *effect,int *restore_attempted, const void *bytes,size_t extent) { if(!effect->attempted) return 0; /* This owner performed no flag mutation. */ if(!effect->returned) return qn_error("policy-partial-flag-outcome-unknown",EBUSY); if(!effect->generation_retained && qn_policy_rejoin_returned_flag(slot,original,effect,bytes,extent)<0) return -1; if(qn_policy_flag_owner_check(slot,effect)<0 || qn_policy_bytes_check(slot,bytes,extent)<0 || qn_policy_restore_original_flags(slot,original,restore_attempted)<0 || qn_policy_flag_owner_check(slot,effect)<0) return -1; return 0; } static int qn_policy_partial_cleanup(void) { struct qn_policy_transition *j=&qn.controller_policy; struct qn_command *compile=&qn.commands[QN_POLICY_COMPILE],*replace=&qn.commands[QN_POLICY_REPLACE]; uint64_t i,errors_before; int result=-1; if(!j->attempted || j->partial_cleanup_attempted) return -1; j->partial_cleanup_attempted=1; if(qn.stage!=QN_HELD || !qn_policy_parser_quiescent(compile,0) || !qn_policy_parser_quiescent(replace,1)) { j->partial_cleanup_refusal=EBUSY; return -1; }
  /* Any executed or unknown replacement keeps actual profile/source debt,
   * even status!=0. Existing never-dispatched/raw-preexec-failure facts only. */ if(qn_owner_check(1)<0) { j->partial_cleanup_refusal=ETIMEDOUT; return -1; } errors_before=qn.errors_used; j->partial_cleanup_active=1; if(qn_policy_partial_file_restore(j->binary_slot,j->binary_original_flags, &j->binary_flag_effect,&j->binary_restore_attempted, compile->stdout_data,compile->stdout_used)<0 || qn_policy_partial_file_restore(j->source_slot,j->source_original_flags, &j->source_flag_effect,&j->source_restore_attempted,j->body,j->body_bytes)<0) goto done;
  /* Reverse only NEW slots of this exact owned attempt. All original gated
   * PROVISION/pidfd/root/baseline slots were registered before slots_begin. */ for(i=qn.slots_used;i>j->slots_begin;i--) { struct qn_slot *s=&qn.slots[i-1]; if(!s->close_attempted) { if(qn_close_slot((int)i-1)<0) goto done; } else if(s->close_result<0 || s->close_errno) { qn_error("policy-partial-owned-close-outcome-unknown",EBUSY); goto done; } } if(qn.errors_used!=errors_before) goto done; if(j->body) { free(j->body); j->body=0; } j->partial_cleanup_complete=1; result=0; done: j->partial_cleanup_active=0;
  /* Never clears first_error, changes HELD, marks replaced/checked/retired,
   * releases the blocked PROVISION child or publishes a positive result. */ return result; }  static int qn_policy_terminal_retire(void) { struct qn_policy_transition *j=&qn.controller_policy; struct qn_command *a=&qn.commands[QN_POLICY_COMPILE],*b=&qn.commands[QN_POLICY_REPLACE]; unsigned i; int result=0; if(!j->attempted) return 0; if(j->retirement_attempted) return qn_error("policy-original-retirement-single-use",EALREADY); j->retirement_attempted=1; if(qn.stage!=QN_RETIRED || !j->checked || !j->replaced) return qn_error("policy-original-terminal-lifetime",EBUSY); for(i=0;i<QN_BORROWS;i++) if(qn.borrows[i].registered && !qn.borrows[i].returned) return qn_error("policy-original-borrow-still-live",EBUSY); if(!a->registered || !a->child_created || a->pending || !a->terminal || !a->exec_proven || a->status || !a->stdout_eof || !a->stderr_eof || !a->stdout_used || a->stdout_used>QN_POLICY_BINARY_LIMIT || a->stderr_used || !b->registered || !b->child_created || b->pending || !b->terminal || !b->exec_proven || b->status || !b->stdout_eof || !b->stderr_eof || b->stdout_used || b->stderr_used || qn_policy_bytes_check(j->source_slot,j->body,j->body_bytes)<0 || qn_policy_bytes_check(j->binary_slot,a->stdout_data,a->stdout_used)<0) return qn_error("policy-original-terminal-parser-and-bytes",EPROTO); if(j->binary_protect_attempted && qn_policy_restore_original_flags(j->binary_slot,j->binary_original_flags, &j->binary_restore_attempted)<0) result=-1; if(j->source_protect_attempted && qn_policy_restore_original_flags(j->source_slot,j->source_original_flags, &j->source_restore_attempted)<0) result=-1; if(result<0) return -1; j->retired=1; return 0; }  static int qn_provision_prepare(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; sigset_t block; struct stat absent; struct rlimit limit; uint64_t before,after; char pid[32]; int null_parent; char *create[]={"/usr/bin/sudo","-n","--","/usr/bin/busctl","call",
    "org.freedesktop.systemd1","/org/freedesktop/systemd1",
    "org.freedesktop.systemd1.Manager","StartTransientUnit","ssa(sv)a(sa(sv))", qn.bootstrap,"fail","5","Description","s","QTT original gated PROVISION",
    "PIDs","au","1",pid,"Slice","s",qn.common,"Delegate","b","false",
    "KillMode","s","control-group","0",0}; if(p->attempted || c->registered) return qn_error("provision-private-launch-single-use",EALREADY);
  /* Both partial native records precede allocation, signal changes or fork. */ memset(p,0,sizeof(*p)); p->attempted=1; p->out_writer=p->err_writer=p->gate_reader=p->gate_writer=-1; p->exec_reader=p->exec_writer=p->image_slot=p->null_slot=p->root_parent=-1;
  p->root_slots[0]=p->root_slots[1]=p->root_slots[2]=-1;
  p->keeper_observations.process_slot=p->keeper_observations.stat_slot=-1;
  p->keeper_observations.namespace_slot=p->keeper_observations.keeper_pid_slot=-1;
  p->keeper_observations.observation_slots[0]=p->keeper_observations.observation_slots[1]=-1;
  p->keeper_observations.observation_slots[2]=-1;
  memset(c,0,sizeof(*c)); c->registered=1; c->pending=1; c->pid_slot=c->stdout_slot=c->stderr_slot=-1; c->start_ns=qn_clock(); if(qn.stage!=QN_PREPARING || qn.common_slot<0 || qn_complete_startup_check()<0 || !c->start_ns || c->start_ns>=qn.cutoff_ns) return -1; sigemptyset(&block); sigaddset(&block,SIGCHLD); sigaddset(&block,SIGINT); sigaddset(&block,SIGTERM); sigaddset(&block,SIGHUP); if(qn_attempt("provision-original-Bash-signal-custody",0)<0 || sigprocmask(SIG_BLOCK,&block,&p->original_mask)<0) return qn_error("provision-original-Bash-signal-custody",errno); p->mask_held=1; if(qn_attempt("provision-original-target-nofile",1)<0 || getrlimit(RLIMIT_NOFILE,&limit)<0 || limit.rlim_cur<64 || limit.rlim_max<64) return qn_error("provision-original-target-nofile",errno?errno:ENOSPC); if(qn_attempt("provision-original-bootstrap-absence",1)<0) return -1; errno=0; if(fstatat(qn.slots[qn.common_slot].fd,qn.bootstrap,&absent,AT_SYMLINK_NOFOLLOW)==0 || errno!=ENOENT) return qn_error("provision-original-bootstrap-collision",errno?errno:EEXIST);
  if(qn_provision_original_inputs()<0 || qn_keeper_observations_prepare()<0) return -1;
  if(qn_provision_prefix_allocation()<0) goto keeper_prefork_failed;
  null_parent=qn_safe_root("/dev"); if(null_parent<0) goto keeper_prefork_failed;
  p->null_slot=qn_provision_null_input(null_parent); if(p->null_slot<0 || qn_fstat(qn.slots[p->null_slot].fd,&absent,"provision-original-null-input")<0 ||
      !S_ISCHR(absent.st_mode)) {
    qn_error("provision-original-null-input",EINVAL);goto keeper_prefork_failed;
  }
  if(qn_pipe_slots(&c->stdout_slot,&p->out_writer)<0 || qn_pipe_slots(&c->stderr_slot,&p->err_writer)<0 || qn_pipe_slots(&p->gate_reader,&p->gate_writer)<0 ||
      qn_pipe_slots(&p->exec_reader,&p->exec_writer)<0 ||
      qn_keeper_observations_prefork_join()<0 ||
      qn_attempt("provision-original-native-fork",0)<0) goto keeper_prefork_failed;
  c->pid=fork();
  if(c->pid<0) {
    qn_error("provision-original-native-fork",errno);goto keeper_prefork_failed;
  }
  if(c->pid==0) qn_provision_child(); c->child_created=1; if(qn_proc_start(c->pid,&before)<0) return -1; c->pid_slot=qn_pidfd_slot(c->pid); if(c->pid_slot<0 || qn_proc_start(c->pid,&after)<0 || before!=after) return qn_error("provision-original-child-generation",ESTALE); c->start_ticks=before; if(qn_close_slot(p->out_writer)<0 || qn_close_slot(p->err_writer)<0 || qn_close_slot(p->gate_reader)<0 || qn_close_slot(p->exec_writer)<0) return -1; if(qn_policy_extend_provision()<0 || qn_provision_role_root()<0) return -1; if(snprintf(pid,sizeof(pid),"%ld",(long)c->pid)>=(int)sizeof(pid)) return qn_error("provision-original-child-pid-extent",EINVAL); p->scope_attempted=1; if(qn_command_run(QN_SCOPE_CREATE,create,0)<0 || qn_provision_scope_show(QN_SCOPE_BEFORE,0)<0) return -1;
  p->prepared=1; return 0;
keeper_prefork_failed:
  if(!p->keeper_observations.partial_close_attempted) {
    p->keeper_observations.partial_close_attempted=1;
    p->keeper_observations.partial_close_result=qn_keeper_observation_slots_close();
  }
  /* No child exists. Retain every original unrelated partial effect/debt;
   * this one-close aggregation grants no borrow, launch or retirement. */
  return -1;
}
static int qn_provision_member(void) { struct qn_command *c=&qn.commands[8]; char pid[32],text[256],expected[256]; int directory,slot,result=-1; size_t n; uint64_t start; if(qn_proc_start(c->pid,&start)<0 || start!=c->start_ticks) return qn_error("provision-original-child-start-after-scope",ESTALE); snprintf(pid,sizeof(pid),"%ld",(long)c->pid); directory=qn_open_component(qn.proc_slot,pid,1,0); if(directory<0) return -1; slot=qn_open_component(directory,"cgroup",0,0); if(slot<0) goto done; if(qn_read_text(slot,text,sizeof(text),&n)<0 || snprintf(expected,sizeof(expected),"0::%s/%s/%s\n",qn.ancestor_group,qn.common,qn.bootstrap)>=(int)sizeof(expected) || strcmp(text,expected)) { qn_error("provision-original-before-target-membership",EXDEV); goto done; } result=0; done: if(slot>=0 && qn_close_slot(slot)<0) result=-1; if(qn_close_slot(directory)<0) result=-1; return result; } static int qn_provision_bind(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; if(!p->prepared || p->bound || p->released || qn.stage!=QN_PREBIRTH || qn_check_slot(qn.ancestor_slot,0)<0 || qn_check_slot(qn.common_slot,0)<0 ||
      qn_check_slot(qn.bootstrap_slot,0)<0 || qn_provision_member()<0 || qn_borrow(QN_PROVISION,c->pid)<0) return -1; p->bound=1; return qn_publish_counters(); }
/* Same original PROVISION terminal DATA, never another launch or wire grant.
 * The original producer uses json.dumps defaults, dataclass field order and
 * one final newline. Earlier mirrored stdout is retained byte-for-byte. */ struct qn_receipt_cursor { const char *at,*end; }; static int qn_receipt_literal(struct qn_receipt_cursor *r,const char *s) { size_t n=strlen(s); if((size_t)(r->end-r->at)<n || memcmp(r->at,s,n)) return -1; r->at+=n; return 0; } static int qn_receipt_string(struct qn_receipt_cursor *r,const char *expected, char *saved,size_t capacity) { size_t used=0; int ended=0; if(qn_receipt_literal(r,"\"")<0) return -1; while(r->at<r->end) { unsigned c=(unsigned char)*r->at++; if(c=='"') { ended=1; break; } if(c<32 || c>126) return -1; if(c=='\\') { if(r->at==r->end) return -1; c=(unsigned char)*r->at++; if(c=='u') { unsigned i,v=0; if(r->end-r->at<4) return -1; for(i=0;i<4;i++) { unsigned x=(unsigned char)*r->at++; if(x>='0'&&x<='9') x-='0'; else if(x>='a'&&x<='f') x=x-'a'+10; else if(x>='A'&&x<='F') x=x-'A'+10; else return -1; v=16*v+x; }
        /* Every selected receipt operand is ordinary ASCII. This does not
         * change the Python JSON owner or accept arbitrary path providers. */ if(v>127) return -1; c=v; } else if(c=='b') c='\b'; else if(c=='f') c='\f'; else if(c=='n') c='\n'; else if(c=='r') c='\r'; else if(c=='t') c='\t'; else if(c!='"'&&c!='\\'&&c!='/') return -1; } if(!c || used>=QN_PATH-1 || (expected && (unsigned char)expected[used]!=c)) return -1; if(saved) { if(used+1>=capacity) return -1; saved[used]=(char)c; } used++; } if(!ended || !used || (expected && expected[used])) return -1; if(saved) saved[used]=0; return 0; } static int qn_receipt_unsigned(struct qn_receipt_cursor *r,uint64_t maximum,uint64_t *out) { const char *first=r->at; uint64_t v=0; if(first==r->end || *first<'0' || *first>'9') return -1; while(r->at<r->end && *r->at>='0' && *r->at<='9') { unsigned d=(unsigned)(*r->at++-'0'); if(v>maximum/10 || (v==maximum/10 && d>maximum%10)) return -1; v=10*v+d; } if(r->at-first>1 && *first=='0') return -1; *out=v; return 0; } static int qn_receipt_number(struct qn_receipt_cursor *r,double maximum,double *out) { const char *start=r->at,*stop; char raw[96],*tail; size_t n; double value; if(r->at==r->end || *r->at<'0'||*r->at>'9') return -1; if(*r->at++!='0') while(r->at<r->end && *r->at>='0'&&*r->at<='9') r->at++; if(r->at<r->end && *r->at=='.') { r->at++; stop=r->at; while(r->at<r->end && *r->at>='0'&&*r->at<='9') r->at++; if(stop==r->at) return -1; } if(r->at<r->end && (*r->at=='e'||*r->at=='E')) { r->at++; if(r->at<r->end&&(*r->at=='+'||*r->at=='-')) r->at++; stop=r->at; while(r->at<r->end&&*r->at>='0'&&*r->at<='9') r->at++; if(stop==r->at) return -1; } n=(size_t)(r->at-start); if(!n || n>=sizeof(raw)) return -1; memcpy(raw,start,n);raw[n]=0; errno=0;value=strtod(raw,&tail); if(errno || tail!=raw+n || !isfinite(value) || value<0 || value>maximum) return -1; *out=value;return 0; } static int qn_receipt_stream(struct qn_receipt_cursor *r,uint64_t expected) { uint64_t value; if(qn_receipt_literal(r,"{\"retention_limit\": ")<0 ||
      qn_receipt_unsigned(r,QN_PROVISION_STREAM,&value)<0 || value!=QN_PROVISION_STREAM || qn_receipt_literal(r,", \"drained_byte_count\": ")<0 || qn_receipt_unsigned(r,QN_PROVISION_STREAM,&value)<0 || value!=expected || qn_receipt_literal(r,", \"cleanup_drained_byte_count\": ")<0 || qn_receipt_unsigned(r,QN_PROVISION_STREAM,&value)<0 || qn_receipt_literal(r,", \"retained_byte_count\": ")<0 || qn_receipt_unsigned(r,QN_PROVISION_STREAM,&value)<0 || value!=expected || qn_receipt_literal(r,", \"overflow\": false, \"complete\": true, \"errors\": []}")<0) return -1; return 0; } static int qn_receipt_terminal(const char *s,int failure,int triggered) { const char *p=s; unsigned action=0; if(!strcmp(s,"NOT_REQUIRED")) return triggered?-1:0; if(!failure) return -1; while(action<2) { const char *name=action?"SIGKILL:":"SIGTERM:"; size_t n=strlen(name); if(strncmp(p,name,n)) return -1; p+=n; if(*p=='0') p++; else { if(!((*p>='A'&&*p<='Z')||(*p>='a'&&*p<='z')||*p=='_')) return -1; do p++; while((*p>='A'&&*p<='Z')||(*p>='a'&&*p<='z')|| (*p>='0'&&*p<='9')||*p=='_'); } if(*p++!=';') return -1; if(!strcmp(p,"TERMINAL:PROVEN")) return 0; action++; } return -1; } static int qn_provision_receipt_decode(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; struct qn_receipt_cursor r; size_t start,i; uint64_t v,parent_pid,stdout_bytes,stderr_bytes; double elapsed,timeout; char phase[96],evidence[QN_PATH],stdout_path[QN_PATH],stderr_path[QN_PATH]; char timeout_state[32],termination[256],failure[96]; int exit_code,negative,failed=0; static const char *const argv_fixed[]={"/usr/bin/sudo","-n",
    "--preserve-env=GITHUB_ACTIONS,GITHUB_EVENT_NAME,GITHUB_REPOSITORY,GITHUB_WORKSPACE,GITHUB_EVENT_PATH,RUNNER_TEMP,GITHUB_REF,GITHUB_REF_NAME,GITHUB_SHA,GITHUB_HEAD_REF,GITHUB_BASE_REF,GITHUB_RUN_ID,GITHUB_RUN_ATTEMPT,LANG,LC_ALL,LD_LIBRARY_PATH,QTT_LINUX_BOOTSTRAP_TICKET",
    "/usr/bin/prlimit","--nofile=64:64","--",0,"-I","-B","-X","utf8",0,
    "--linux-preflight-provision","--phase",0}; const char *temporary=qn_provision_environment_value("RUNNER_TEMP"); if(p->receipt_attempted) return qn_error("provision-original-receipt-single-use",EALREADY); p->receipt_attempted=1; if(!p->released || !c->terminal || !c->exec_proven || !c->stdout_eof || !c->stderr_eof || !p->exec_done || !p->prefix_merged || !temporary || !c->stdout_data || !c->stdout_used || c->stdout_used>QN_PROVISION_STREAM || c->stdout_data[c->stdout_used-1]!='\n') goto bad;
  /* Only the original producer's final complete receipt line is decoded.
   * Earlier binary or multiline output remains in the original owned buffer. */ start=c->stdout_used-1; while(start && c->stdout_data[start-1]!='\n') start--; r=(struct qn_receipt_cursor){c->stdout_data+start,c->stdout_data+c->stdout_used-1}; if(snprintf(phase,sizeof(phase),"%s-provision",qn.phase)>=(int)sizeof(phase) || snprintf(evidence,sizeof(evidence),"%s/%s",temporary,p->root_name)>=(int)sizeof(evidence) || snprintf(stdout_path,sizeof(stdout_path),"%s/evidence/command-1.stdout.bin",evidence)>=(int)sizeof(stdout_path) || snprintf(stderr_path,sizeof(stderr_path),"%s/evidence/command-1.stderr.bin",evidence)>=(int)sizeof(stderr_path)) goto bad;
  /* Closed canonical key order rejects omissions, extras and duplicate keys.
   * Every value follows the unchanged original serializer and typed receipt. */ if(qn_receipt_literal(&r,"{\"ordinary_provision_receipt\": {\"schema_version\": 1, \"run_id\": ")<0 || qn_receipt_string(&r,p->root_name,0,0)<0 || qn_receipt_literal(&r,", \"phase\": ")<0 || qn_receipt_string(&r,phase,0,0)<0 || qn_receipt_literal(&r,", \"command_index\": 1, \"argv\": [")<0) goto bad; for(i=0;i<sizeof(argv_fixed)/sizeof(*argv_fixed);i++) { const char *expected=i==6?p->image:i==11?p->script:i==14?qn.phase:argv_fixed[i]; if((i && qn_receipt_literal(&r,", ")<0) || qn_receipt_string(&r,expected,0,0)<0) goto bad; } if(qn_receipt_literal(&r,"], \"cwd\": ")<0 || qn_receipt_string(&r,QN_SOURCE_WORKSPACE,0,0)<0 || qn_receipt_literal(&r,", \"pid\": ")<0 || qn_receipt_unsigned(&r,INT_MAX,&parent_pid)<0 || !parent_pid || parent_pid==(uint64_t)c->pid || parent_pid==(uint64_t)qn.pid || qn_receipt_literal(&r,", \"platform\": \"posix\", \"start_time_utc\": ")<0 || qn_receipt_string(&r,0,0,0)<0 || qn_receipt_literal(&r,", \"end_time_utc\": ")<0 || qn_receipt_string(&r,0,0,0)<0 || qn_receipt_literal(&r,", \"elapsed_monotonic_seconds\": ")<0 || qn_receipt_number(&r,3720.0,&elapsed)<0 || qn_receipt_literal(&r,", \"native_exit_code\": ")<0) goto bad; negative=r.at<r.end&&*r.at=='-';if(negative)r.at++; if(qn_receipt_unsigned(&r,INT_MAX,&v)<0 || (negative&&!v)) goto bad; exit_code=negative?-(int)v:(int)v; if(qn_receipt_literal(&r,", \"start_failure_class\": null, \"timeout_seconds_or_null\": ")<0 || qn_receipt_number(&r,3720.0,&timeout)<0 || timeout<=0 || qn_receipt_literal(&r,", \"timeout_state\": ")<0 || qn_receipt_string(&r,0,timeout_state,sizeof(timeout_state))<0 || (strcmp(timeout_state,"NOT_TRIGGERED")&&strcmp(timeout_state,"TRIGGERED")) || qn_receipt_literal(&r,", \"termination_state\": ")<0 || qn_receipt_string(&r,0,termination,sizeof(termination))<0 || qn_receipt_literal(&r,", \"stdout_path\": ")<0 || qn_receipt_string(&r,stdout_path,0,0)<0 ||
      qn_receipt_literal(&r,", \"stderr_path\": ")<0 || qn_receipt_string(&r,stderr_path,0,0)<0 || qn_receipt_literal(&r,", \"stdout_byte_count\": ")<0 || qn_receipt_unsigned(&r,QN_PROVISION_STREAM,&stdout_bytes)<0 || qn_receipt_literal(&r,", \"stderr_byte_count\": ")<0 || qn_receipt_unsigned(&r,QN_PROVISION_STREAM,&stderr_bytes)<0 || stdout_bytes>QN_PROVISION_COMBINED-stderr_bytes || qn_receipt_literal(&r,", \"stdout_required_markers\": [], \"stdout_marker_state\": \"NOT_REQUIRED\", \"stderr_was_nonempty\": ")<0 || qn_receipt_literal(&r,stderr_bytes?"true":"false")<0 || qn_receipt_literal(&r,", \"failure_class\": ")<0) goto bad; if(r.end-r.at>=4&&!memcmp(r.at,"null",4)) r.at+=4; else { failed=1; if(qn_receipt_string(&r,0,failure,sizeof(failure))<0 || (strcmp(failure,"ENGVR_NATIVE_EXIT_NONZERO")&&strcmp(failure,"ENGVR_PROCESS_TIMEOUT")&& strcmp(failure,"ENGVR_ATOMIC_RECEIPT_WRITE_FAILED")&&strcmp(failure,"ENGVR_REQUIRED_MARKER_MISSING")) || (!strcmp(failure,"ENGVR_PROCESS_TIMEOUT")&&strcmp(timeout_state,"TRIGGERED"))) goto bad; } if((!failed&&exit_code) || qn_receipt_terminal(termination,failed,!strcmp(timeout_state,"TRIGGERED"))<0 || c->status!=((!failed&&!exit_code)?0:1) || qn_receipt_literal(&r,", \"registered_argv\": [], \"removed_environment_keys\": [], \"fixed_environment_controls\": [], \"output_observation\": {\"combined_output_grant\": ")<0 || qn_receipt_unsigned(&r,QN_PROVISION_COMBINED,&v)<0 || v!=QN_PROVISION_COMBINED || qn_receipt_literal(&r,", \"stdout\": ")<0 || qn_receipt_stream(&r,stdout_bytes)<0 || qn_receipt_literal(&r,", \"stderr\": ")<0 || qn_receipt_stream(&r,stderr_bytes)<0 || qn_receipt_literal(&r,"}}, \"evidence\": ")<0 || qn_receipt_string(&r,evidence,0,0)<0 || qn_receipt_literal(&r,"}")<0 || r.at!=r.end) goto bad; p->receipt_offset=start;p->receipt_length=c->stdout_used-start; p->receipt_parent_pid=(pid_t)parent_pid;p->receipt_parent_status=exit_code; p->receipt_decoded=1;return 0; bad: return qn_error("provision-original-parent-receipt-shape-or-association",EPROTO); }
static int qn_provision_release_observe(void) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; struct pollfd ports[4]; if(!p->prepared || !p->bound || !p->mask_held || qn.stage!=QN_RUNNING || !c->child_created || qn.borrows[QN_PROVISION].pid!=c->pid || !qn.borrows[QN_PROVISION].registered || qn.borrows[QN_PROVISION].returned) return qn_error("provision-original-release-binding",EPROTO); if(p->observed) return c->status; /* Same receipt; never another launch. */ if(p->release_attempted) return qn_error("provision-original-release-single-use",EALREADY); p->release_attempted=1; if(qn_complete_startup_check()<0 || qn_provision_scope_show(QN_SCOPE_RELEASE,1)<0 || qn_provision_member()<0 || qn_provision_directories_check()<0 ||
      qn_policy_provision_release_check()<0 ||
      qn_keeper_observations_release_join()<0 ||
      qn_provision_root_publish()<0 ||
      qn_gate_write_original(c,p->gate_writer)<0) return -1; p->released=1; if(qn_close_slot(p->gate_writer)<0) return -1; while(!c->terminal || !c->stdout_eof || !c->stderr_eof || !p->exec_done) { uint64_t now=qn_clock(),remaining; int ready,timeout; if(!now || now>=qn.cutoff_ns) return qn_error("provision-original-native-supervision-timeout",ETIMEDOUT); remaining=qn.cutoff_ns-now; timeout=(int)((remaining+999999U)/1000000U); ports[0]=(struct pollfd){c->stdout_eof?-1:qn.slots[c->stdout_slot].fd,POLLIN,0}; ports[1]=(struct pollfd){c->stderr_eof?-1:qn.slots[c->stderr_slot].fd,POLLIN,0}; ports[2]=(struct pollfd){c->terminal?-1:qn.slots[c->pid_slot].fd,POLLIN,0}; ports[3]=(struct pollfd){p->exec_done?-1:qn.slots[p->exec_reader].fd,POLLIN,0}; if(qn_attempt("provision-original-native-supervision-poll",0)<0) return -1; ready=poll(ports,4,timeout); if(ready<0) return qn_error("provision-original-native-supervision-poll",errno); if(!ready) return qn_error("provision-original-native-supervision-timeout",ETIMEDOUT); if(ports[0].revents&(POLLIN|POLLHUP)) if(qn_capture_one(c,0)<0) return -1; if(ports[1].revents&(POLLIN|POLLHUP)) if(qn_capture_one(c,1)<0) return -1;
    if(c->stdout_used>QN_PROVISION_STREAM || c->stderr_used>QN_PROVISION_STREAM || c->stdout_used>QN_PROVISION_COMBINED-c->stderr_used) return qn_error("provision-original-output-partition",EFBIG); if(!p->exec_done && (ports[3].revents&(POLLIN|POLLHUP))) { unsigned char *packet=(unsigned char *)&p->exec_errno,suffix; size_t request=sizeof(p->exec_errno)-p->exec_used; ssize_t n; n=qn_read(p->exec_reader,request?packet+p->exec_used:&suffix,request?request:1); if(n<0) return -1; if(!n) { if(!p->exec_used) c->exec_proven=1; else if(p->exec_used!=sizeof(p->exec_errno) || p->exec_errno<=0) return qn_error("provision-original-exec-port",EPROTO); p->exec_done=1; } else if(request) p->exec_used+=(size_t)n; else return qn_error("provision-original-exec-port-suffix",EPROTO); } if(!c->terminal && (ports[2].revents&POLLIN)) { struct qn_terminal_observation *observed=&c->terminal_observation; if(qn_waitid_original(observed,c->pid_slot,"provision-original-terminal-WNOWAIT")<0) return -1; if(observed->info.si_pid!=c->pid || observed->info.si_code!=CLD_EXITED) return qn_error("provision-original-terminal-receipt",EPROTO); c->terminal=1; c->status=observed->info.si_status; } { unsigned i; for(i=0;i<4;i++) if(ports[i].revents&(POLLNVAL|POLLERR)) return qn_error("provision-original-native-supervision-port",EIO); } } if(qn_provision_prefix_merge()<0) return -1; if(!c->exec_proven || !atomic_load_explicit(&p->prefix_journal->exec_attempted,memory_order_acquire) || atomic_load_explicit(&p->prefix_journal->failed,memory_order_acquire)) return qn_error("provision-original-exec",p->exec_errno?p->exec_errno:EPROTO);
  /* Normal body nonzero remains a terminal STATUS, not a lost native error.
   * SIGCHLD stays blocked and waitid left this exact child waitable.
   */ if(qn_provision_receipt_decode()<0) return -1; p->observed=1; c->end_ns=qn_clock(); if(qn_publish_counters()<0) return -1; return c->status; } static int qn_provision_return(int terminal_status) { struct qn_provision *p=&qn.provision; struct qn_command *c=&qn.commands[8]; struct qn_borrow *borrow=&qn.borrows[QN_PROVISION]; struct qn_terminal_observation *observed=&borrow->return_observation; int status,result=0; unsigned i; int slots[10]; if(p->return_attempted) return qn_error("provision-original-return-single-use",EALREADY); p->return_attempted=1; if(qn_owner_check(0)<0 || !p->observed || !p->mask_held || !c->pending || !c->terminal || !c->exec_proven || !c->stdout_eof || !c->stderr_eof || terminal_status!=c->status || !borrow->registered || borrow->returned || borrow->pid!=c->pid || borrow->start_ticks!=c->start_ticks || borrow->pid_slot<0 || !p->prefix_merged || qn_complete_startup_check()<0) return qn_error("provision-original-return-terminal-and-EOF-required",EPROTO); if(qn_waitid_original(observed,borrow->pid_slot,"provision-original-return-WNOWAIT")<0) return -1; if(observed->info.si_pid!=c->pid || observed->info.si_code!=CLD_EXITED || observed->info.si_status!=terminal_status) return qn_error("provision-original-return-native-status",EPROTO); p->reap_attempted=1; if(qn_attempt("provision-original-one-reap",0)<0 || waitpid(c->pid,&status,0)!=c->pid || !WIFEXITED(status) || WEXITSTATUS(status)!=terminal_status) return qn_error("provision-original-one-reap",errno?errno:EPROTO); p->reaped=1; c->pending=0; borrow->terminal_code=observed->info.si_code;
  borrow->terminal_status=observed->info.si_status;
  if(qn_keeper_observations_retire()<0) result=-1;
  slots[0]=c->stdout_slot; slots[1]=c->stderr_slot; slots[2]=c->pid_slot; slots[3]=borrow->pid_slot; slots[4]=p->out_writer; slots[5]=p->err_writer; slots[6]=p->gate_reader; slots[7]=p->gate_writer; slots[8]=p->exec_reader; slots[9]=p->exec_writer; for(i=0;i<10;i++) if(slots[i]>=0 && !qn.slots[slots[i]].close_attempted && qn_close_slot(slots[i])<0) result=-1; if(result<0) return -1; borrow->returned=1;
  /* Only a C-owned exact reap permits the original signal mask restoration. */ if(qn_attempt("provision-original-mask-restoration",0)<0 || sigprocmask(SIG_SETMASK,&p->original_mask,0)<0) return qn_error("provision-original-mask-restoration",errno); p->mask_held=0; qn.stage=QN_TERMINAL; return qn_publish_counters(); } static int qn_provision_storage_close(void) { struct qn_provision *p=&qn.provision; unsigned i; if(!p->attempted) return 0;
  if(!p->reaped || !qn.borrows[QN_PROVISION].returned || p->mask_held ||
     !p->keeper_observations.retired)
    return qn_error("provision-original-storage-live-debt",EBUSY); if(p->prefix_journal) { if(p->prefix_unmap_attempted) return qn_error("provision-original-one-unmap",EALREADY); p->prefix_unmap_attempted=1; if(qn_attempt("provision-original-prefix-munmap",0)<0 || munmap(p->prefix_journal,p->prefix_bytes)<0) return qn_error("provision-original-prefix-munmap",errno); p->prefix_journal=0; } for(i=0;i<p->environment_count;i++) { free(p->environment[i]); p->environment[i]=0; } return 0; }  static int qn_suffix_command(unsigned occurrence,struct qn_manager_fields *fields) { char *unit; int show; char *show_argv[10]; char *stop_argv[7]; if(qn.stage!=QN_TERMINAL || occurrence>=6 || occurrence!=(unsigned)qn.command_occurrence) return -1; unit=(occurrence%2)?qn.common:qn.bootstrap; show=occurrence<2 || occurrence>=4; if(!show && ((occurrence==2&&!qn.bootstrap_present) || (occurrence==3&&!qn.common_present))) { ++qn.command_occurrence; return 0; /* Actual native absence, no command effect. */ } show_argv[0]="/usr/bin/sudo"; show_argv[1]="-n"; show_argv[2]="--"; show_argv[3]="/usr/bin/systemctl"; show_argv[4]="show"; show_argv[5]="--no-pager"; show_argv[6]="--all"; show_argv[7]="--property=Id,LoadState,Transient,InvocationID,ControlGroup,ActiveState"; show_argv[8]=unit; show_argv[9]=0; stop_argv[0]="/usr/bin/sudo"; stop_argv[1]="-n"; stop_argv[2]="--"; stop_argv[3]="/usr/bin/systemctl"; stop_argv[4]="stop"; stop_argv[5]=unit; stop_argv[6]=0; if(qn_command_run(occurrence+2,show?show_argv:stop_argv,0)<0) return -1;
  ++qn.six_calls; ++qn.command_occurrence; return show?qn_manager_decode(qn.commands[occurrence+2].stdout_data,fields):0; } static int qn_manager_native_join(const struct qn_manager_fields *f,int common,int final) { char expected[160]; struct stat current; int parent,slot,present; const char *unit=common?qn.common:qn.bootstrap; if(strcmp(f->id,unit)) return qn_error("original-manager-unit-identity",ESTALE); parent=common?qn.ancestor_slot:qn.common_slot; slot=common?qn.common_slot:qn.bootstrap_slot; if((final?qn_check_held_parent(parent):qn_check_slot(parent,0))<0 || qn_attempt("original-manager-native-path",1)<0) return -1; errno=0; present=fstatat(qn.slots[parent].fd,unit,&current,AT_SYMLINK_NOFOLLOW)==0; if(!present) { if(errno!=ENOENT || (strcmp(f->active,"inactive")&&strcmp(f->active,"failed")) || f->group[0]) return qn_error("original-manager-native-absence",errno?errno:EPROTO); } else { if(final || strcmp(f->transient,"yes") || !qn_hex32(f->invocation)) return qn_error("original-manager-native-present-state",EPROTO); if((common ? snprintf(expected,sizeof(expected),"%s/%s",qn.ancestor_group,qn.common) : snprintf(expected,sizeof(expected),"%s/%s/%s",qn.ancestor_group,qn.common,qn.bootstrap)) >=(int)sizeof(expected)) return qn_error("original-manager-native-group-extent",ENAMETOOLONG); if(strcmp(f->group,expected) || (common && strcmp(f->invocation,qn.invocation))) return qn_error("original-manager-native-generation",ESTALE); if(slot<0) return qn_error("original-bootstrap-generation-not-held",ESTALE); { struct qn_version v=qn_stat_version(&current); if(!qn_identity_equal(&v,&qn.slots[slot].handle_before)) return qn_error("original-manager-native-handle-identity",ESTALE); } if(qn_empty_directory(parent,unit,slot,0)<0) return -1; } if(common) qn.common_present=present; else qn.bootstrap_present=present; return 0; } static int qn_retire(void) { struct qn_manager_fields fields; unsigned i; if(qn.stage!=QN_TERMINAL || !qn.prefix_unmounted || qn.command_occurrence) return -1;
  for(i=0;i<2;i++) if(qn_suffix_command(i,&fields)<0 || qn_manager_native_join(&fields,i==1,0)<0) return -1; for(i=2;i<4;i++) if(qn_suffix_command(i,0)<0) return -1; for(i=4;i<6;i++) if(qn_suffix_command(i,&fields)<0 || qn_manager_native_join(&fields,i==5,1)<0) return -1; qn.stage=QN_RETIRED; return qn_publish_counters(); } static int qn_prefix_unmounted(const char *prefix) { int directory=-1,slot=-1,result=-1; char pid[32],expected[160],*text=0,*line; size_t n; if(!qn.provision.receipt_decoded || !qn.provision.observed || !qn.provision.reaped || !qn.borrows[QN_PROVISION].returned || qn.provision.receipt_parent_pid<=0 || snprintf(expected,sizeof(expected),"/run/qtt%ldn%" PRIu64 "ordinary/prefix", (long)qn.provision.receipt_parent_pid,qn.origin_ns)>=(int)sizeof(expected) || !prefix || strcmp(prefix,expected)) return qn_error("original-parent-prefix-receipt-association",EPROTO); if(qn.stage!=QN_TERMINAL || prefix[0]!='/' || strlen(prefix)>=QN_PATH || strchr(prefix,' ') || strchr(prefix,'\\') || strstr(prefix,"/../") || strstr(prefix,"/./")) return -1; snprintf(pid,sizeof(pid),"%ld",(long)qn.pid); directory=qn_open_component(qn.proc_slot,pid,1,0); if(directory<0) return -1; slot=qn_open_component(directory,"mountinfo",0,0); if(slot<0) goto done; text=malloc(QN_DATA); if(!text) { qn_error("native-mountinfo-storage",ENOMEM); goto done; } if(qn_read_text(slot,text,QN_DATA,&n)<0) goto done; line=text; while(*line) { char *end=strchr(line,'\n'),*p=line,*field_end; unsigned field; if(!end) { qn_error("native-mountinfo-shape",EPROTO); goto done; } *end=0; for(field=1;field<5;field++) { p=strchr(p,' '); if(!p) { qn_error("native-mountinfo-field",EPROTO); goto done; } ++p; } field_end=strchr(p,' '); if(!field_end) { qn_error("native-mountinfo-mountpoint",EPROTO); goto done; } *field_end=0;
    /* Source-selected prefixes use only the ordinary ASCII unit spelling and
     * slash. Encoded/escaped mounts at or below it are rejected, not decoded
     * permissively into another locator.
     */ if(!strcmp(p,prefix) || (!strncmp(p,prefix,strlen(prefix)) && p[strlen(prefix)]=='/')) { qn_error("ordinary-prefix-still-mounted",EBUSY); goto done; } line=end+1; } qn.prefix_unmounted=1; result=0; done: free(text); if(slot>=0 && qn_close_slot(slot)<0) result=-1; if(directory>=0 && qn_close_slot(directory)<0) result=-1; return result; } static int qn_finish(void) { unsigned i; int result=0; if(qn_owner_check(0)<0 || qn.stage!=QN_RETIRED || qn.command_occurrence!=6 || qn.six_calls<4 || qn.six_calls>6) return -1; for(i=0;i<QN_BORROWS;i++) if(qn.borrows[i].registered && !qn.borrows[i].returned) return qn_error("native-borrow-not-returned",EBUSY); if(qn_startup_check()<0 || qn_provision_storage_close()<0 || qn_policy_terminal_retire()<0) return -1; for(i=0;i<qn.input_count;i++) { if(qn_flag_effect(i,0,1)<0 || qn_flag_effect(i,1,1)<0) return -1; } for(i=0;i<qn.catalogue_count;i++) { if(qn_catalogue_flag_effect(i,0,1)<0 || qn_catalogue_flag_effect(i,1,1)<0) return -1; } if(qn_startup_mode_loan(0,0,qn.snapshot_root_slot,1)<0) return -1;
  /* Reverse dependency order. Explicit one-close is the only release path;
   * a loader destructor neither manufactures settlement nor performs cleanup.
   */ for(i=(unsigned)qn.slots_used;i;i--) { struct qn_slot *s=&qn.slots[i-1]; if(!s->close_attempted && qn_close_slot((int)i-1)<0) result=-1; } for(i=0;i<qn.catalogue_count;i++) { free(qn.catalogues[i].names); qn.catalogues[i].names=0; } if(result<0 || qn.first_error) return -1; if(qn.controller_policy.body) { if(!qn.controller_policy.retired) return qn_error("policy-original-retained-source-still-live",EBUSY); free(qn.controller_policy.body); qn.controller_policy.body=0; } qn.stage=QN_CLOSED; return qn_publish_counters(); }
/* Finite argv shape: only fixed operations of this original native owner.
 * No executable/vector/path grant is accepted from QTT serialized inputs.
 */ static size_t qn_arguments(WORD_LIST *words,char **argv,size_t capacity) { size_t n=0; for(;words;words=words->next) { if(n==capacity || !words->word || !words->word->word) return capacity+1; argv[n++]=words->word->word; } return n; } static int qn_role_number(const char *s,enum qn_role *role) { if(!strcmp(s,"CHECKER")) *role=QN_CHECKER; else if(!strcmp(s,"PROVISION")) *role=QN_PROVISION; else if(!strcmp(s,"PARENT")) *role=QN_PARENT; else if(!strcmp(s,"RECEIVER")) *role=QN_RECEIVER; else return -1; return 0; } int qtt_ordinary_native_builtin(WORD_LIST *words) { char *a[16]; size_t n=qn_arguments(words,a,16); int result=-1; uint64_t value; enum qn_role role; if(n==8 && !strcmp(a[0],"init")) result=qn_init(a[1],a[2],a[3],a[4],a[5],a[6],a[7]); else if(n==1 && !strcmp(a[0],"prebirth")) result=qn_common_acquire(); else if(n==1 && !strcmp(a[0],"startup-check")) { result=qn.provision.prepared?qn_provision_release_observe():qn_startup_check();
    /* Positive body status is DATA. Native failure remains first_error/HELD
     * and cannot be returned as an observed body-status receipt. */ return result<0?1:result; } else if(n==8 && !strcmp(a[0],"startup-catalog")) result=qn_catalogue_register(a); else if(n==4 && !strcmp(a[0],"startup-absence")) result=qn_absence_register(a); else if(n==8 && !strcmp(a[0],"startup-register")) { struct qn_input *p; int s,t; struct stat ss,ts; struct qn_version sp,sh,bp,bh; unsigned i; if(qn.stage!=QN_PREPARING || qn.catalogue_attempted || qn.input_count>=QN_INPUTS || qn_decimal(a[3],UINT64_C(134217728),&value)<0 || qn_expected_version(a[4],&sp)<0 || qn_expected_version(a[5],&sh)<0 || qn_expected_version(a[6],&bp)<0 || qn_expected_version(a[7],&bh)<0 || !S_ISREG(sp.mode) || !S_ISREG(sh.mode) || !S_ISREG(bp.mode) || !S_ISREG(bh.mode) || !qn_identity_equal(&sp,&sh) || !qn_identity_equal(&bp,&bh) || sp.size<0 || bp.size<0 || (uint64_t)sp.size!=value || (uint64_t)bp.size!=value) goto done; p=&qn.inputs[qn.input_count++]; memset(p,0,sizeof(*p)); p->occupied=1; p->source_slot=p->snapshot_slot=-1; p->length=value; s=qn_regular_absolute(a[1]); p->source_slot=s; t=qn_regular_absolute(a[2]); p->snapshot_slot=t; if(s<0 || t<0 || qn_fstat(qn.slots[s].fd,&ss,"startup-source-register")<0 || qn_fstat(qn.slots[t].fd,&ts,"startup-snapshot-register")<0 || !qn_version_equal(&sp,&qn.slots[s].path_before) || !qn_version_equal(&sh,&qn.slots[s].handle_before) || !qn_version_equal(&bp,&qn.slots[t].path_before) || !qn_version_equal(&bh,&qn.slots[t].handle_before) || qn_identity_equal(&qn.slots[s].handle_before,&qn.slots[t].handle_before) || ss.st_size<0 || ts.st_size<0 || (uint64_t)ss.st_size!=value || (uint64_t)ts.st_size!=value || qn_current_flags(s,&p->original_flags)<0 || qn_current_flags(t,&p->baseline_original_flags)<0 || qn_compare_slots(s,t,value)<0) goto done; for(i=0;i+1<qn.input_count;i++) { struct qn_input *old=&qn.inputs[i]; if(qn_identity_equal(&sp,&old->source_version) || qn_identity_equal(&sp,&old->snapshot_version) || qn_identity_equal(&bp,&old->source_version) ||
          qn_identity_equal(&bp,&old->snapshot_version)) { qn_error("startup-active-operand-alias",EXDEV); goto done; } } snprintf(p->source,sizeof(p->source),"%s",a[1]); snprintf(p->snapshot,sizeof(p->snapshot),"%s",a[2]); p->source_version=qn_stat_version(&ss); p->snapshot_version=qn_stat_version(&ts); if(qn_flag_effect((unsigned)qn.input_count-1,0,0)<0 || qn_flag_effect((unsigned)qn.input_count-1,1,0)<0 || qn_immutable_slot(s,&p->flags)<0 || qn_immutable_slot(t,&p->baseline_flags)<0 || qn_compare_slots(s,t,value)<0) goto done; result=qn_publish_counters(); } else if(n==3 && !strcmp(a[0],"startup-borrow") && qn_role_number(a[1],&role)==0 && qn_decimal(a[2],INT_MAX,&value)==0) result=qn_borrow(role,(pid_t)value); else if(n==3 && !strcmp(a[0],"startup-return") && qn_role_number(a[1],&role)==0 && qn_decimal(a[2],255,&value)==0) result=qn_return(role,(int)value); else if(n==2 && !strcmp(a[0],"prefix-unmounted")) result=qn_prefix_unmounted(a[1]); else if(n==1 && !strcmp(a[0],"native-empty")) result=qn_native_empty(0); else if(n==1 && !strcmp(a[0],"native-absent")) result=qn_native_empty(1); else if(n==1 && !strcmp(a[0],"retire")) result=qn_retire(); else if(n==1 && !strcmp(a[0],"startup-close")) result=qn_finish(); done:
  /* Actual errno/counter data is retained in this original living owner. This
   * return is not a PASS marker or an accepted manifest. Invocation errors
   * before ownership do not silently initialize an admission.
   */ if(result<0) return 1; return 0; } char *qtt_ordinary_native_doc[] = {
  "Private existing-workflow native custody; requires qualified original ABI.",
  "Only the original Source-gated PROVISION vector is continued; no caller-selected native command is provided.", 0 }; struct builtin qtt_ordinary_native_struct = {
  "qtt_ordinary_native", qtt_ordinary_native_builtin, BUILTIN_ENABLED, qtt_ordinary_native_doc, "qtt_ordinary_native private-fixed-operation", 0 }; void qtt_ordinary_native_builtin_unload(char *name) { (void)name;
  /* GNU Bash 5.2 treats this as void, so it CANNOT veto unloading. The fixed
   * shell never calls enable -d on a live/HELD owner. This hook intentionally
   * performs no descriptor cleanup. Actual process exit ends a HELD pin's
   * lifetime; nothing claims that lifetime persists after holder exit.
   */ }
'''
# QTT_ORDINARY_NATIVE_C_DATA_END_20261008_V1

from dataclasses import dataclass
import os
import pathlib
import re
import subprocess
from typing import Callable, Sequence


def _ordinary_rp5a_manager_label_source_v1(raw, _f):
 # Pure common Source parsing; the actual physical owner supplies the bytes.
 _f._preflight_require_v1(type(raw) is bytes,
  'ORDINARY_R_ACTUAL_MANAGER_LABEL_SAFE_LITERAL')
 selected = re.fullmatch(rb'([A-Za-z0-9_.:/-]{1,256})(?: \((?:enforce|complain)\))?\n', raw)
 _f._preflight_require_v1(selected is not None,
  'ORDINARY_R_ACTUAL_MANAGER_LABEL_SAFE_LITERAL')
 return selected[1].decode('ascii', 'strict')


def _ordinary_rp5a_manager_credentials_source_v1(status, _f):
 _f._preflight_require_v1(type(status) is bytes,
  'ORDINARY_R_ORIGINAL_ROOT_READ_CREDENTIAL_FIELDS')
 fields = {}
 for line in status.splitlines():
  key, separator, value = line.partition(b':')
  if key not in (b'Uid', b'CapEff', b'CapPrm', b'CapBnd'):
   continue
  _f._preflight_require_v1(separator and key not in fields,
   'ORDINARY_R_ORIGINAL_ROOT_READ_CREDENTIAL_FIELDS')
  fields[key] = value.strip()
 _f._preflight_require_v1(set(fields) == {b'Uid', b'CapEff', b'CapPrm', b'CapBnd'}
  and fields[b'Uid'].split() == [b'0'] * 4
  and all(re.fullmatch(rb'[0-9A-Fa-f]{1,16}', fields[key]) is not None
   and int(fields[key], 16) & (1 << 19) for key in (b'CapEff', b'CapPrm', b'CapBnd')),
  'ORDINARY_R_ACTUAL_EXISTING_KERNEL_MANAGER_READ_AUTHORITY')


def _ordinary_rp5a_manager_result_source_v1(before, label, raw, status, after, _f):
 _f._preflight_require_v1(before == after,
  'ORDINARY_R_ACTUAL_EXISTING_KERNEL_MANAGER_READ_AUTHORITY')
 return (before, label, raw, status)


def _run_pr152_repository_read(
    repo_root: pathlib.Path, arguments: Sequence[str]
) -> subprocess.CompletedProcess[str]:
    """The closed PR152 read profile; discovery failure is not a child result."""
    if isinstance(arguments, (str, bytes)) or not isinstance(arguments, Sequence):
        raise ValueError("PR152 read arguments must be a string sequence")
    if not all(type(value) is str for value in arguments):
        raise ValueError("PR152 read arguments must be exact strings")
    selected = tuple(arguments)
    fixed = {
        ("ls-files", "-z"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        ("branch", "--show-current"),
        ("rev-parse", "--abbrev-ref", "HEAD"),
    }
    if selected not in fixed:
        if (len(selected) != 6 or selected[:5] != (
            "diff", "--no-ext-diff", "--no-textconv", "--unified=0", "--"
        )):
            raise ValueError("unadmitted PR152 Git read vector")
        path = selected[5]
        if (not path or any(character in path for character in "\\\x00\r\n:")
                or path.startswith("/")
                or any(part in {"", ".", ".."} for part in path.split("/"))):
            raise ValueError("invalid literal PR152 diff path")
    return _run_repository_read_process(repo_root, selected)

BRANCH_CONTEXT_ENV_CANDIDATES = (
    "GITHUB_HEAD_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF",
    "BRANCH_NAME",
    "CI_COMMIT_REF_NAME",
)

CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    "DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_ACTIVE"
)
REPAIR_BRANCH_PREFIX = "repair/"
MAIN_CUMULATIVE_BRANCH_PREFIX = "repair/main-cumulative-"
CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH = "pr-ci-runtime-parallel-cache-timeout"
PR208_CI_RUNTIME_RATIONALIZATION_BRANCH = "pr208-ci-runtime-rationalization"
NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_BRANCH = (
    "repair/no-runtime-custody-and-ci-dependency-boundary"
)
ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH = (
    "repair/st12-architecture-independent-oracle-closure"
)
ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_CHANGED_PATHS = frozenset(
    {
        "tools/independent_validate_qku_computation_control_plane_architecture.py",
        "tools/ci_branch_context.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH = (
    "repair/st12-inherited-math-row-receipt-closure"
)
ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_CHANGED_PATHS = frozenset(
    {
        "tools/qku_independent_math_row_receipt.py",
        "tools/independent_validate_qku_computation_control_plane_accounting.py",
        "tools/independent_validate_qku_computation_control_plane_execution.py",
        "tools/independent_validate_qku_computation_control_plane_d.py",
        "tools/independent_validate_qku_computation_control_plane_model_risk.py",
        "tools/independent_validate_qku_computation_control_plane_quantum.py",
        "tools/ci_branch_context.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        "tests/tools/test_qku_independent_math_row_receipt.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/security/"
        "test_input_validation.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_CHANGED_PATHS = frozenset(
    {
        "tools/validate_no_runtime_artifacts.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tools/validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tools/ci_branch_context.py",
        "tests/tools/test_ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
VALIDATION_INFRASTRUCTURE_BRANCHES = frozenset(
    {
        "pr-ci-fastfail-validation-context-preflight",
        CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH,
        PR208_CI_RUNTIME_RATIONALIZATION_BRANCH,
        NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_BRANCH,
    }
)
VALIDATION_INFRASTRUCTURE_CHANGED_PATHS = frozenset(
    {
        ".gitattributes",
        ".github/workflows/qtt_validation.yml",
        "docs/master_plan/generated/PR208_ChangedAreaRoutingPolicy.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_CrossPlatformPathInvariant.report.json",
        "docs/master_plan/generated/PR208_FinalSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_parameter_default_value_materialization_gate/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_implementation_bridge/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "agent_consumable_parameter_default_registry/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "agent_default_binding_universal_intake_gate/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/constants.py",
        "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults/report.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
        "src/qtt/stage1_prediction_markets/"
        "qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix/report.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_bundle_boundary_state_contract.py",
        "tests/atomicrows/test_atomicrows_bundle_materialization_manifest.py",
        "tests/atomicrows/test_atomicrows_sha_freeze_final_readiness_state_contract.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/fail_closed/test_pytest_fresh_basetemp_helper.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/"
        "test_pr163_c_repeat_run_determinism.py",
        "tests/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/"
        "test_pr164_repeat_run_determinism.py",
        "tests/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/"
        "test_pr166_sm_idempotence.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_cross_platform_path_invariant.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        "tests/tools/test_validation_inventory.py",
        "tools/ci_branch_context.py",
        "tools/changed_area_validation_router.py",
        "tools/cross_platform_path_invariant.py",
        "tools/repo_path_refs.py",
        "tools/run_pytest_fresh_basetemp.py",
        "tools/run_validation_gates.py",
        "tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/validate_validation_inventory.py",
        "tools/validate_ci_branch_context_matrix.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tools/validate_nested_validator_contracts.py",
        "tools/validate_repair_pr_changed_file_scope.py",
        "tools/validation_inventory.py",
        "tools/validation_reliability.py",
    }
)
PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr163-c-main-branch-context-after-merge"
)
PR159R_BRANCH_CONTEXT_REPAIR_BRANCH = "repair/pr159r-branch-context-relaxation"
PR159R_DETACHED_HEAD_REPAIR_BRANCH = "repair/pr159r-detached-head-branch-context"
PR159S_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr159s-open-intake-branch-context-relaxation"
)
PR160_MAIN_ANCESTRY_REPAIR_BRANCH = "repair/pr160-main-ancestry-after-pr176"
PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "repair/pr160-main-push-branch-context-relaxation"
)
PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH = (
    "repair/main-pr166-sm2-bounded-idempotence-ci"
)
PR152_HELPER_CLI_TEMP_REPO_GIT_STATUS_REPAIR_BRANCH = (
    "repair-pr152-helper-cli-temp-repo-git-status"
)
VALIDATION_EXECUTION_BRANCHES = frozenset(
    {
        PR152_HELPER_CLI_TEMP_REPO_GIT_STATUS_REPAIR_BRANCH,
    }
)
ST12H_IMPLEMENTATION_BRANCH = (
    "agent/st12h-validation-currentization-operations-publication"
)
S1_LAUNCH_GRAPH_IMPLEMENTATION_BRANCH = (
    "s1-launch-graph-materialization-01"
)
S1_PIT_DATA_PHASE_A_01_IMPLEMENTATION_BRANCH = "s1-pit-data-phase-a-01"
S1_PLUGIN_PACKAGE_CURRENTIZATION_BRANCH = (
    "s1-plugin-package-currentization-01"
)
F12_EXACT_TIME_COMPOSITION_BRANCH = "f12-exact-time-composition"
F14_PRIVATE_EVIDENCE_JOIN_BRANCH = "f14-private-evidence-join"

F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH = "f13-private-clock-storage-replay"
ENGVR_IMPLEMENTATION_BRANCH = (
    "hardening/eng-validation-reliability-windows-text-integrity"
)
ENGVR_NORMAL_CHANGED_PATHS = frozenset(
    {
        ".gitattributes",
        "tools/validation_reliability.py",
        "tools/run_validation_gates.py",
        "tools/run_pytest_fresh_basetemp.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tools/ci_branch_context.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/fail_closed/test_pytest_fresh_basetemp_helper.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
    }
)
ENGVR_TRIGGERED_CONDITIONAL_CHANGED_PATHS = frozenset(
    {
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
ENGVR_CHANGED_PATHS = frozenset(
    (*ENGVR_NORMAL_CHANGED_PATHS, *ENGVR_TRIGGERED_CONDITIONAL_CHANGED_PATHS)
)
OWNER_AUTHORIZED_VALIDATION_BRANCHES = frozenset(
    {
        "agent/st12a-contract-envelope",
        "agent/st12b-contextual-computability-v3",
        "agent/st12c-deterministic-receipts-accounting-v1",
        "agent/st12e-capability-guard",
        "agent/st12d-mode-snapshot-boundary",
        "agent/st12f-evidence-model-risk-v1",
        "agent/st12g-existing-owner-projections-v2",
        ST12H_IMPLEMENTATION_BRANCH,
        S1_LAUNCH_GRAPH_IMPLEMENTATION_BRANCH,
        S1_PIT_DATA_PHASE_A_01_IMPLEMENTATION_BRANCH,
        S1_PLUGIN_PACKAGE_CURRENTIZATION_BRANCH,
        F12_EXACT_TIME_COMPOSITION_BRANCH,
        F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH,
        F14_PRIVATE_EVIDENCE_JOIN_BRANCH,
        ENGVR_IMPLEMENTATION_BRANCH,
        ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH,
        ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH,
    }
)
IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_BRANCH = (
    "hardening/all-idempotence-runtime-containment-audit"
)
IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_CHANGED_PATHS = frozenset(
    {
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tests/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/"
        "test_pr163_c_repeat_run_determinism.py",
        "tests/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/"
        "test_pr164_repeat_run_determinism.py",
        "tests/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/"
        "test_pr166_sm_idempotence.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tools/validation_inventory.py",
    }
)
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS = {
    "repair-pr153r-redo-report-determinism": 153,
    PR152_HELPER_CLI_TEMP_REPO_GIT_STATUS_REPAIR_BRANCH: 152,
    "repair/pr153s-source-value-capture-closure-classifier": 153,
    "pr154-atomicrows-parameter-default-value-materialization-gate": 154,
    "repair/pr154-post-merge-pytest-context-hygiene": 154,
    "pr155-agent-consumable-parameter-default-registry": 155,
    "pr156-agent-default-binding-universal-intake-gate": 156,
    "pr157-pr154-atomicrows-fillpath-owner-agent-bridge": 157,
    "pr158-owner-response-atomicrows-selection-readiness-bridge": 158,
    "pr159-official-source-retry-atomicrows-source-completion-bridge": 159,
    "pr159r-exact-source-locator-value-unit-capture": 159,
    "pr159s-open-source-intelligence-candidate-completion": 159,
    PR159R_BRANCH_CONTEXT_REPAIR_BRANCH: 159,
    PR159R_DETACHED_HEAD_REPAIR_BRANCH: 159,
    PR159S_BRANCH_CONTEXT_REPAIR_BRANCH: 159,
    "pr160-pr154-split-reclassification-route-closure-bridge": 160,
    PR160_MAIN_ANCESTRY_REPAIR_BRANCH: 160,
    PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH: 160,
    "pr161a-atomicrows-pr154-value-state-materialization-bridge": 161,
    "repair/pr161a-atomicrows-pr154-value-state-materialization-bridge": 161,
    "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge": 161,
    "repair/pr161b-master-plan-residual-candidate-coverage-assimilation-bridge": 161,
    "pr161c-qku-residual-candidate-assimilation-fill-campaign": 161,
    "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization": 161,
    "pr161e-replay-paper-outcome-capture-scenario-learning-bridge": 161,
    "pr161f-replay-paper-executor-input-run-artifact-generation": 161,
    "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge": 162,
    "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate": 162,
    "pr162b-qku-formula-algorithm-solver-market-scope-materialization": 162,
    "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage": 162,
    "pr162d-aggressive-qku-candidate-materialization-agent-routing": 162,
    "pr162d-r1-external-formula-data-quantum-acquisition-expansion": 162,
    "pr162r-a-replay-paper-executability-classification-audit": 162,
    "pr162d-r2a-real-computable-formulations-redo": 162,
    "pr162r-generic-replay-paper-adapter-rerun": 162,
    "pr162r-b-replay-paper-data-binding-completion": 162,
    "pr163-generic-paper-adapter-capture-framework": 163,
    "pr163-b-paired-replay-paper-concurrent-executor": 163,
    "pr163-c-pretrade-infrastructure-rejection-remediation": 163,
    PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH: 163,
    "pr164-review-provenance-qku-canonical-coverage-audit": 164,
    "pr165-evidence-backed-scoring-ranking": 165,
    "pr165-b-condition-scoped-negative-memory": 165,
    "pr165-c-replay-paper-memory-consumer-integration": 165,
    "pr165-d-scenario-qku-combination-selection": 165,
    "pr166-sf-r2-targeted-conversion-repair-retest": 166,
    "pr166-sm3-score-memory-refresh-v3": 166,
    PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH: 166,
}
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CONTEXT_ALLOWANCES = {
    159: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
    160: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
    161: frozenset({PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH}),
}
PR152_CURRENTIZATION_AFTER_FASTFAIL_MERGE_CHANGED_PATHS = frozenset(
    {
        ".github/workflows/qtt_validation.yml",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/constants.py",
        "src/qtt/stage1_prediction_markets/"
        "grand_global_debug_logical_consistency_audit/report.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tools/ci_branch_context.py",
    }
)
PR159_BRANCH = "pr159-official-source-retry-atomicrows-source-completion-bridge"
PR159_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159_",
    "src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge/",
    "tests/stage1_prediction_markets/pr159_official_source_completion_bridge/",
)
PR160_BRANCH = "pr160-pr154-split-reclassification-route-closure-bridge"
PR160_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR160_",
    "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/",
    "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/",
)
PR160_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr160_split_reclassification_route_closure.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR161A_BRANCH = "pr161a-atomicrows-pr154-value-state-materialization-bridge"
PR161A_REPAIR_BRANCH = "repair/pr161a-atomicrows-pr154-value-state-materialization-bridge"
PR161A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR161A_",
    "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/",
    "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/schemas/pr161a_",
    "tests/stage1_prediction_markets/atomicrows_pr154_value_state/",
)
PR161A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/__init__.py",
        "tools/build_pr161a_atomicrows_pr154_value_state_materialization.py",
        "tools/validate_pr161a_atomicrows_pr154_value_state_materialization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR161B_BRANCH = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
PR161B_REPAIR_BRANCH = "repair/pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
PR161B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR161B_",
    "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/",
    "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/",
)
PR161B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161b_master_plan_residual_candidate_coverage.py",
        "tools/validate_pr161b_master_plan_residual_candidate_coverage.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR161C_BRANCH = "pr161c-qku-residual-candidate-assimilation-fill-campaign"
PR161C_GENERATED_REPORT_FILENAMES = (
    "PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT.report.json",
    "PR161C_PR161APrimaryEntityDiagnostic.report.json",
    "PR161C_PR161AFieldValueFacetDiagnostic.report.json",
    "PR161C_PR161BQueueDiagnostic.report.json",
    "PR161C_PR161BToPR161AFieldCoverageDiagnostic.report.json",
    "PR161C_QKUSupplementalArtifactScout.report.json",
    "PR161C_QKUResidualTypeBreakdown.report.json",
    "PR161C_QKUResidualDiagnosticJustification.report.json",
    "PR161C_QKUFillLaneBreakdown.report.json",
    "PR161C_QKUAuthorityAndProvenanceBreakdown.report.json",
    "PR161C_QKUAgentAndWorkflowBreakdown.report.json",
    "PR161C_QKUMarketBreakdown.report.json",
    "PR161C_QKULaunchStageBreakdown.report.json",
    "PR161C_QKUClassicalQuantumHybridBreakdown.report.json",
    "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    "PR161C_QKUExpandedRecordAccounting.report.json",
    "PR161C_QKUDefaultMaterializationCoverage.report.json",
    "PR161C_QKUNumericDefaultMaterialization.report.json",
    "PR161C_QKUFormulaDefaultMaterialization.report.json",
    "PR161C_QKUAlgorithmConfigMaterialization.report.json",
    "PR161C_QKUOptimizerDefaultMaterialization.report.json",
    "PR161C_QKUOwnerFallbackDefaultMaterialization.report.json",
    "PR161C_QKUOnlineSourceMaterialization.report.json",
    "PR161C_QKUAgentLaunchReadinessMaterialization.report.json",
    "PR161C_QKUCanonicalRegistry.report.json",
    "PR161C_QKUAliasMap.report.json",
    "PR161C_QKUTypeTaxonomy.report.json",
    "PR161C_QKUResidualAssimilationRegistry.report.json",
    "PR161C_QKUResidualAssimilationDelta.report.json",
    "PR161C_QKUFormulaAlgorithmAssimilation.report.json",
    "PR161C_QKUParameterRangeAssimilation.report.json",
    "PR161C_QKUQuantumAssimilation.report.json",
    "PR161C_QKUQuantumResidualTrace.report.json",
    "PR161C_QKUClassicalHybridAssimilation.report.json",
    "PR161C_QKUReplayPaperRouteBridge.report.json",
    "PR161C_QKUAgentConsumptionBridge.report.json",
    "PR161C_QKUUpstreamDownstreamTraceability.report.json",
    "PR161C_QKUWorkflowProcessBridge.report.json",
    "PR161C_QKUDownstreamPRFileBridge.report.json",
    "PR161C_QKUOrchestrationCompleteness.report.json",
    "PR161C_QKUOrchestrationGraph.report.json",
    "PR161C_QKUOrchestrationGraphEdges.report.json",
    "PR161C_QKUOrchestrationGraphCompleteness.report.json",
    "PR161C_QKUGraphQualityMetrics.report.json",
    "PR161C_QKUIsolatedNodeAudit.report.json",
    "PR161C_QKUSourceUpgradeQueue.report.json",
    "PR161C_QKUOnlineScoutQueue.report.json",
    "PR161C_QKUSourceIntakeAcceptancePolicy.report.json",
    "PR161C_QKUOnlineRetrievalAudit.report.json",
    "PR161C_QKUMasterInventoryBridge.report.json",
    "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "PR161C_QKUPR154CompatibilityBridge.report.json",
    "PR161C_QKUMarketClassificationInventory.report.json",
    "PR161C_QKULaunchStageClassification.report.json",
    "PR161C_QKUClassicalQuantumHybridInventory.report.json",
    "PR161C_QKUAlgorithmFormulaStrategyInventory.report.json",
    "PR161C_QKUQuantumForwardOptimizationInventory.report.json",
    "PR161C_QKUAgentRetrievalIndex.report.json",
    "PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json",
    "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    "PR161C_QKUCrossMarketReuseIndex.report.json",
    "PR161C_QKURangeOptimizerMaterializationAudit.report.json",
    "PR161C_QKUFallbackDefaultExhaustionAudit.report.json",
    "PR161C_QKUFinalAssimilationSummary.report.json",
    "PR161C_ForbiddenAuthorityScan.report.json",
    "PR161C_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161C_QKUReportShardManifest.report.json",
    "PR161C_BranchContextAndDeterministicAudit.report.json",
)
PR161C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161c_qku_report_shards/",
    "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation/",
    "tests/stage1_prediction_markets/qku_residual_candidate_assimilation/",
)
PR161C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161c_qku_residual_candidate_assimilation.py",
        "tools/validate_pr161c_qku_residual_candidate_assimilation.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161C_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161D_BRANCH = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"
PR161D_GENERATED_REPORT_FILENAMES = (
    "PR161D_QKU_CANDIDATE_QUALITY_PREFLIGHT_RECEIPT.report.json",
    "PR161D_QKUOnlineSearchCapabilityReceipt.report.json",
    "PR161D_QKUQualityScoreRegistry.report.json",
    "PR161D_QKUScoreComponentBreakdown.report.json",
    "PR161D_QKUQualityLaneClassification.report.json",
    "PR161D_QKUReplayPaperPriorityQueue.report.json",
    "PR161D_QKUReplayPaperScenarioInputs.report.json",
    "PR161D_QKUOnlineEnrichmentClusterMap.report.json",
    "PR161D_QKUOnlineEnrichmentCoverage.report.json",
    "PR161D_QKUOnlineSourceCandidateRegistry.report.json",
    "PR161D_QKUQuantumPriorityQueue.report.json",
    "PR161D_QKUClassicalBaselinePriorityQueue.report.json",
    "PR161D_QKUHybridArbitrationPriorityQueue.report.json",
    "PR161D_QKUAtomicRowsPR154PriorityBridge.report.json",
    "PR161D_QKUAgentTaskQueue.report.json",
    "PR161D_QTTAgentRoleNetworkRegistry.report.json",
    "PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "PR161D_QKUAgentLayerCoverage.report.json",
    "PR161D_QKUAgentRoleCoverageGaps.report.json",
    "PR161D_QKUStage1Day1PriorityIndex.report.json",
    "PR161D_QKUOwnerReviewQueue.report.json",
    "PR161D_QKUGraphConsumptionAudit.report.json",
    "PR161D_QKUScoringPolicyConsumptionAudit.report.json",
    "PR161D_QKUScenarioOutcomeMatrix.report.json",
    "PR161D_QKUOrderConditionScenarioRegistry.report.json",
    "PR161D_QKUCombinationCandidateRegistry.report.json",
    "PR161D_QKUCombinationScenarioMap.report.json",
    "PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "PR161D_QKUCombinationGenerationBoundedness.report.json",
    "PR161D_QKUMarketBundleActivationPolicy.report.json",
    "PR161D_QKUMarketBundleActivationDashboardOptions.report.json",
    "PR161D_QKUMarketBundleDormancyQueue.report.json",
    "PR161D_QKUMarketActiveBundleSet.report.json",
    "PR161D_QKUAgentRoleBundleSlice.report.json",
    "PR161D_QKUAgentRoleBundleReferenceFanout.report.json",
    "PR161D_QKUCategoryRankingRegistry.report.json",
    "PR161D_QKUCategoryTopListIndex.report.json",
    "PR161D_QKUCategoryRankingBreakdown.report.json",
    "PR161D_QKUFutureProfitabilityPatternFields.report.json",
    "PR161D_QKUResultBackedRankingSlots.report.json",
    "PR161D_QKUForbiddenAuthorityScan.report.json",
    "PR161D_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161D_ReportShardManifest.report.json",
    "PR161D_FinalSummary.report.json",
)
PR161D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161d_qku_candidate_quality_shards/",
    "src/qtt/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/",
    "tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/",
)
PR161D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
        "tools/validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161D_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161E_BRANCH = "pr161e-replay-paper-outcome-capture-scenario-learning-bridge"
PR161E_GENERATED_REPORT_FILENAMES = (
    "PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json",
    "PR161E_ReplayPaperResultArtifactDiscovery.report.json",
    "PR161E_ResultAuthenticityClassification.report.json",
    "PR161E_ReplayResultPacketValidation.report.json",
    "PR161E_PaperResultPacketValidation.report.json",
    "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "PR161E_QKUBundleResultLedger.report.json",
    "PR161E_QKUReplayPaperProfitabilityLedger.report.json",
    "PR161E_QKUScenarioResultAttribution.report.json",
    "PR161E_QKUResultBackedRankingUpdateCandidates.report.json",
    "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json",
    "PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
    "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json",
    "PR161E_ResultConfidenceGate.report.json",
    "PR161E_OwnerReviewResultPromotionQueue.report.json",
    "PR161E_AgentOutcomeTaskQueue.report.json",
    "PR161E_OnlineMetricCandidateIntake.report.json",
    "PR161E_OpenIntakeCandidateBridge.report.json",
    "PR161E_MissingValueCandidateMaterialization.report.json",
    "PR161E_QKUGraphTraceabilityBridge.report.json",
    "PR161E_QKUCoverageAndOrphanAudit.report.json",
    "PR161E_ForbiddenAuthorityScan.report.json",
    "PR161E_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161E_SharedDictionary.report.json",
    "PR161E_ReportShardManifest.report.json",
    "PR161E_FinalSummary.report.json",
)
PR161E_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161e_replay_paper_outcome_capture_shards/",
    "src/qtt/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/",
    "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/",
)
PR161E_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161e_replay_paper_outcome_capture_scenario_learning.py",
        "tools/validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161E_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR161F_BRANCH = "pr161f-replay-paper-executor-input-run-artifact-generation"
PR161F_GENERATED_REPORT_FILENAMES = (
    "PR161F_ReplayPaperExecutorInputPreflightReceipt.report.json",
    "PR161F_ExecutorCapabilityDiscovery.report.json",
    "PR161F_HistoricalDataCandidateDiscovery.report.json",
    "PR161F_DatasetAuthorityClassification.report.json",
    "PR161F_ExecutorInputRegistry.report.json",
    "PR161F_ReplayRunRequestRegistry.report.json",
    "PR161F_PaperRunRequestRegistry.report.json",
    "PR161F_PairedReplayPaperRunPlan.report.json",
    "PR161F_RunArtifactEnvelopeRegistry.report.json",
    "PR161F_SyntheticSmokeRunArtifactRegistry.report.json",
    "PR161F_RealNonLiveRunArtifactRegistry.report.json",
    "PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "PR161F_QuantumClassicalHybridRunPlan.report.json",
    "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json",
    "PR161F_AgentRunTaskQueue.report.json",
    "PR161F_OwnerReviewRunReadinessQueue.report.json",
    "PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "PR161F_QTTAgentRoleIOContract.report.json",
    "PR161F_QTTAgentHandoffMatrix.report.json",
    "PR161F_QTTAgentFailureResponseMatrix.report.json",
    "PR161F_QTTAgentTaskReceiptLedger.report.json",
    "PR161F_QTTAgentCommunicationProtocol.report.json",
    "PR161F_QTTAgentKPIReadinessBridge.report.json",
    "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
    "PR161F_QTTAgentOwnerEscalationQueue.report.json",
    "PR161F_OnlineCandidateIntake.report.json",
    "PR161F_MissingValueCandidateMaterialization.report.json",
    "PR161F_QKUGraphTraceabilityBridge.report.json",
    "PR161F_ForbiddenAuthorityScan.report.json",
    "PR161F_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161F_SharedDictionary.report.json",
    "PR161F_ReportShardManifest.report.json",
    "PR161F_SizeAudit.report.json",
    "PR161F_FinalSummary.report.json",
)
PR161F_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr161f_replay_paper_executor_input_run_artifact_generation_shards/",
    "src/qtt/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/",
    "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/",
)
PR161F_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr161f_replay_paper_executor_input_run_artifact_generation.py",
        "tools/validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation/validator.py",
        "src/qtt/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization/validator.py",
        "src/qtt/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/validator.py",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR161F_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162_BRANCH = "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge"
PR162_GENERATED_REPORT_FILENAMES = (
    "PR162_FinalSummary.report.json",
    "PR162_SharedDictionary.report.json",
    "PR162_NonLiveDatasetDiscovery.report.json",
    "PR162_DataAuthorityAndProvenanceGate.report.json",
    "PR162_ReplayDataAdapterContract.report.json",
    "PR162_PaperDataAdapterContract.report.json",
    "PR162_AdapterCapabilityDiscovery.report.json",
    "PR162_SyntheticVsRealNonLiveSeparation.report.json",
    "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
    "PR162_ResultPacketReadinessHandoffCandidate.report.json",
    "PR162_PR161EIngestionHandoffCandidate.report.json",
    "PR162_QKUArtifactCoverageBridge.report.json",
    "PR162_QTTAgentExecutorHandoffBridge.report.json",
    "PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
    "PR162_ExternalCandidateIntakeRegistry.report.json",
    "PR162_ForbiddenAuthorityScan.report.json",
    "PR162_QKUQuantumExecutionReadinessBridge.report.json",
    "PR162_QKUQuantumProblemEncodingBlueprint.report.json",
    "PR162_QuantumParameterRangeCandidateRegistry.report.json",
    "PR162_QuantumBackendFitCandidateMatrix.report.json",
    "PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
    "PR162_QuantumReplayPaperWorkOrderQueue.report.json",
    "PR162_QuantumLiveModeControlPlaneBridge.report.json",
    "PR162_QuantumLatencyLivePathReadinessBridge.report.json",
    "PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
    "PR162_ReportShardManifest.report.json",
)
PR162_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162_safe_nonlive_replay_paper_quantum_forward_shards/",
    "src/qtt/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge/",
    "tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge/",
)
PR162_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162A_BRANCH = "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate"
PR162A_GENERATED_REPORT_FILENAMES = (
    "PR162A_FinalSummary.report.json",
    "PR162A_SharedDictionary.report.json",
    "PR162A_SourceDiscoveryCandidateRegistry.report.json",
    "PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json",
    "PR162A_DatasetMaterializationManifest.report.json",
    "PR162A_DatasetAuthorityGate.report.json",
    "PR162A_DatasetProvenanceAccessRightsLedger.report.json",
    "PR162A_DatasetSafetyAndForbiddenPathScan.report.json",
    "PR162A_DatasetLifecycleStateRegistry.report.json",
    "PR162A_DatasetSchemaNormalizationContract.report.json",
    "PR162A_NormalizedDatasetInventory.report.json",
    "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json",
    "PR162A_MarketScenarioQKUMappingMatrix.report.json",
    "PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
    "PR162A_PR162AdapterRerunReadinessBridge.report.json",
    "PR162A_PR163ReadinessBlockerStatus.report.json",
    "PR162A_QuantumQKUDatasetFeatureBridge.report.json",
    "PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
    "PR162A_QTTAgentDatasetHandoffBridge.report.json",
    "PR162A_MissingValueCandidateRegistry.report.json",
    "PR162A_ForbiddenAuthorityScan.report.json",
    "PR162A_ReportShardManifest.report.json",
)
PR162A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162a_safe_repo_local_nonlive_dataset_shards/",
    "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/",
    "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/",
    "data/stage1_prediction_markets/nonlive_datasets/pr162a/",
)
PR162A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162A_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162B_BRANCH = "pr162b-qku-formula-algorithm-solver-market-scope-materialization"
PR162B_GENERATED_REPORT_FILENAMES = (
    "PR162B_FinalSummary.report.json",
    "PR162B_SharedDictionary.report.json",
    "PR162B_FormulaSourceRetrievalTargetMatrix.report.json",
    "PR162B_QKUExecutionClassificationAudit.report.json",
    "PR162B_QKUMarketClassificationRegistry.report.json",
    "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
    "PR162B_QKUDormancyRegistry.report.json",
    "PR162B_QKUTradeRoleRegistry.report.json",
    "PR162B_QKUMarketInputFieldRequirementMatrix.report.json",
    "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    "PR162B_QKUMarketClassificationCoverageAudit.report.json",
    "PR162B_QKUFormulaCoverageAudit.report.json",
    "PR162B_QKUFormulaRegistry.report.json",
    "PR162B_QKUAlgorithmRegistry.report.json",
    "PR162B_QKUObjectiveFunctionRegistry.report.json",
    "PR162B_QKUConstraintRegistry.report.json",
    "PR162B_QKUParameterValueRegistry.report.json",
    "PR162B_QKUParameterRangeScaleRegistry.report.json",
    "PR162B_QKUTradableValueCandidateRegistry.report.json",
    "PR162B_QKUSolverMappingRegistry.report.json",
    "PR162B_QKUExecutableComputeContractRegistry.report.json",
    "PR162B_QKUFormulaTestVectorRegistry.report.json",
    "PR162B_QKUAlgorithmTestVectorRegistry.report.json",
    "PR162B_QKUFormulaImplementationBindingRegistry.report.json",
    "PR162B_QKUFormulaBindingProofMatrix.report.json",
    "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
    "PR162B_QuantumSolverSmokeExecutionReport.report.json",
    "PR162B_AgentFormulaConsumerRoutingMatrix.report.json",
    "PR162B_LiveModeFormulaGateStatus.report.json",
    "PR162B_MetadataOnlyBlockerAudit.report.json",
    "PR162B_PR162CDataRequirementHandoff.report.json",
    "PR162B_ForbiddenAuthorityScan.report.json",
    "PR162B_ReportShardManifest.report.json",
)
PR162B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/pr162b_qku_formula_solver_market_scope_shards/",
    "src/qtt/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization/",
    "tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization/",
)
PR162B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162B_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162C_BRANCH = "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
PR162C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162C_",
    "docs/master_plan/generated/PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT.report.json",
    "docs/master_plan/generated/pr162c_multisource_safe_nonlive_dataset_shards/",
    "src/qtt/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/",
    "tests/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/",
)
PR162C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
        "tools/validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_BRANCH = "pr162d-aggressive-qku-candidate-materialization-agent-routing"
PR162D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_",
    "docs/master_plan/generated/pr162d_aggressive_qku_candidate_materialization_agent_routing_shards/",
    "src/qtt/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing/",
    "tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing/",
)
PR162D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
        "tools/validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_R1_BRANCH = "pr162d-r1-external-formula-data-quantum-acquisition-expansion"
PR162D_R1_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_R1_",
    "src/qtt/stage1_prediction_markets/"
    "pr162d_r1_external_formula_data_quantum_acquisition_expansion/",
    "tests/stage1_prediction_markets/"
    "pr162d_r1_external_formula_data_quantum_acquisition_expansion/",
)
PR162D_R1_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
        "tools/validate_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162R_A_BRANCH = "pr162r-a-replay-paper-executability-classification-audit"
PR162R_A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162R_A_",
    "src/qtt/stage1_prediction_markets/"
    "pr162r_a_replay_paper_executability_classification_audit/",
    "tests/stage1_prediction_markets/"
    "pr162r_a_replay_paper_executability_classification_audit/",
)
PR162R_A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_a_replay_paper_executability_classification_audit.py",
        "tools/validate_pr162r_a_replay_paper_executability_classification_audit.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    }
)
PR162D_R2A_BRANCH = "pr162d-r2a-real-computable-formulations-redo"
PR162D_R2A_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162D_R2A_",
    "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/",
    "tests/stage1_prediction_markets/pr162d_r2a_real_formulations/",
)
PR162D_R2A_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162d_r2a_real_formulations.py",
        "tools/validate_pr162d_r2a_real_formulations.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR162R_BRANCH = "pr162r-generic-replay-paper-adapter-rerun"
PR162R_GENERATED_REPORT_FILENAMES = (
    "PR162R_InputConsumptionAudit.report.json",
    "PR162R_CandidatePacketV1IngestionLedger.report.json",
    "PR162R_CandidatePacketSchemaCompatibilityAudit.report.json",
    "PR162R_QKUComputabilityClassificationMatrix.report.json",
    "PR162R_QKUNonPlaceholderCompletionAudit.report.json",
    "PR162R_FormulationCallableImportAudit.report.json",
    "PR162R_FormulationSmokeExecutionLedger.report.json",
    "PR162R_SourceCandidateMaterializationQueue.report.json",
    "PR162R_OnlineSourceScoutQueue.report.json",
    "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
    "PR162R_MissingDataBindingActionQueue.report.json",
    "PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "PR162R_PaperAdapterInputPacketRegistry.report.json",
    "PR162R_ReplayRunRequestCandidateQueue.report.json",
    "PR162R_PaperRunRequestCandidateQueue.report.json",
    "PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json",
    "PR162R_LatencyPrecomputeRoutingMatrix.report.json",
    "PR162R_RouteTriageCrosswalkConsumptionAudit.report.json",
    "PR162R_MarketSpecificQKUAdapterIndex.report.json",
    "PR162R_CommandActionQKUBindingMatrix.report.json",
    "PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "PR162R_PR163PaperAdapterHandoffSeed.report.json",
    "PR162R_PR164ReviewProvenanceHandoffSeed.report.json",
    "PR162R_PR165ScoringRankingHandoffSeed.report.json",
    "PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json",
    "PR162R_OrphanCandidateReportAudit.report.json",
    "PR162R_NoReplayPaperResultPacketAudit.report.json",
    "PR162R_NoLiveOrderProfitAuthorityAudit.report.json",
    "PR162R_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
    "PR162R_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR162R_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR162R_Old548CompatibilityTrace.report.json",
    "PR162R_FinalSummary.report.json",
    "PR162R_DecisionAndNextPRRecommendation.report.json",
    "PR162R_ReportManifest.report.json",
)
PR162R_ALLOWED_CHANGED_PATH_PREFIXES = (
    "src/qtt/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/",
    "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/",
)
PR162R_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_generic_replay_paper_adapter_rerun.py",
        "tools/validate_pr162r_generic_replay_paper_adapter_rerun.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        *(
            f"docs/master_plan/generated/{filename}"
            for filename in PR162R_GENERATED_REPORT_FILENAMES
        ),
    }
)
PR162R_B_BRANCH = "pr162r-b-replay-paper-data-binding-completion"
PR162R_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162R_B_",
    "docs/master_plan/generated/pr162r_b_shards/",
    "src/qtt/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
    "tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
    "tests/fixtures/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion/",
)
PR162R_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162r_b_replay_paper_data_binding_completion.py",
        "tools/validate_pr162r_b_replay_paper_data_binding_completion.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/validators.py",
        "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun/test_orphan_audit.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_BRANCH = "pr163-generic-paper-adapter-capture-framework"
PR163_B_BRANCH = "pr163-b-paired-replay-paper-concurrent-executor"
PR163_C_BRANCH = "pr163-c-pretrade-infrastructure-rejection-remediation"
PR164_BRANCH = "pr164-review-provenance-qku-canonical-coverage-audit"
PR165_BRANCH = "pr165-evidence-backed-scoring-ranking"
PR165_B_BRANCH = "pr165-b-condition-scoped-negative-memory"
PR165_C_BRANCH = "pr165-c-replay-paper-memory-consumer-integration"
PR165_D_BRANCH = "pr165-d-scenario-qku-combination-selection"
PR166_S_BRANCH = "pr166-s-replay-paper-scenario-retest-execution"
PR166_SM_BRANCH = "pr166-sm-score-memory-refresh-from-pr166-s-results"
PR166_SF_BRANCH = "pr166-sf-repair-materialization-before-retest"
PR166_S2_BRANCH = "pr166-s2-replay-paper-retest-loop-v2"
PR166_SM2_BRANCH = "pr166-sm2-score-memory-refresh-v2"
PR166_SF_R2_BRANCH = "pr166-sf-r2-targeted-conversion-repair-retest"
PR166_SM3_BRANCH = "pr166-sm3-score-memory-refresh-v3"
PR166_Q_BRANCH = "pr166-q-quantum-classical-hybrid-comparator"
PR166_QB_BRANCH = "pr166-qb-bounded-nonlive-quantum-optimizer-benchmark"
PR166_QC_BRANCH = "pr166-qc-quantum-selected-replay-paper-retest"
PR162E_Q_BRANCH = "pr162e-q-quantum-automapper"
PR162E_BRANCH = "pr162e-plugin-framework"
PR167_BRANCH = "pr167-open-trade-simulator-integration"
PR168_GFP_BRANCH = "pr168-gfp-global-formula-discovery-real-computation"
PR165_D2_BRANCH = "pr165-d2-score-refreshed-scenario-selection-v2"
PR165_D3_BRANCH = "pr165-d3-quantum-aware-scenario-selection-v3"
PR165_D2_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH = (
    "pr165-d2-main-push-branch-context-repair"
)
PR163_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_",
    "docs/master_plan/generated/pr163_shards/",
    "src/qtt/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework/",
    "tests/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework/",
)
PR163_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_generic_paper_adapter_capture_framework.py",
        "tools/validate_pr163_generic_paper_adapter_capture_framework.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_B_",
    "docs/master_plan/generated/pr163_b_shards/",
    "src/qtt/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor/",
    "tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor/",
)
PR163_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_b_paired_replay_paper_concurrent_executor.py",
        "tools/validate_pr163_b_paired_replay_paper_concurrent_executor.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR163_C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR163_C_",
    "docs/master_plan/generated/pr163_c_shards/",
    "src/qtt/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation/",
    "tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation/",
)
PR163_C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/test_pr161a_branch_context.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
        "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR164_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR164_",
    "docs/master_plan/generated/pr164_shards/",
    "src/qtt/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit/",
    "tests/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit/",
)
PR164_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr164_review_provenance_qku_canonical_coverage_audit.py",
        "tools/validate_pr164_review_provenance_qku_canonical_coverage_audit.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_",
    "docs/master_plan/generated/pr165_shards/",
    "src/qtt/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking/",
    "tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking/",
)
PR165_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_evidence_backed_scoring_ranking.py",
        "tools/validate_pr165_evidence_backed_scoring_ranking.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_B_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_B_",
    "docs/master_plan/generated/pr165_b_shards/",
    "src/qtt/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory/",
    "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory/",
)
PR165_B_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_b_condition_scoped_negative_memory.py",
        "tools/validate_pr165_b_condition_scoped_negative_memory.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_C_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_C_",
    "docs/master_plan/generated/pr165_c_shards/",
    "src/qtt/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/",
    "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration/",
)
PR165_C_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
        "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR165_D_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_D_",
    "docs/master_plan/generated/pr165_d_shards/",
    "src/qtt/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/",
    "tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection/",
)
PR165_D_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_d_scenario_qku_combination_selection.py",
        "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR166_S_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_S_",
    "docs/master_plan/generated/pr166_s_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_s_replay_paper_scenario_retest_execution/",
    "tests/stage1_prediction_markets/"
    "pr166_s_replay_paper_scenario_retest_execution/",
)
PR166_S_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_s_replay_paper_scenario_retest_execution.py",
        "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_SM_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_SM_",
    "docs/master_plan/generated/pr166_sm_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_sm_score_memory_refresh_from_pr166_s_results/",
    "tests/stage1_prediction_markets/"
    "pr166_sm_score_memory_refresh_from_pr166_s_results/",
)
PR166_SM_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
        "tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_SF_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_SF_",
    "docs/master_plan/generated/pr166_sf_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_sf_repair_materialization_before_retest/",
    "tests/stage1_prediction_markets/"
    "pr166_sf_repair_materialization_before_retest/",
)
PR166_SF_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_sf_repair_materialization_before_retest.py",
        "tools/validate_pr166_sf_repair_materialization_before_retest.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/validator.py",
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/"
        "test_pr165_d2_optional_pr166_sf_handling.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_S2_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_S2_",
    "docs/master_plan/generated/pr166_s2_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_s2_replay_paper_retest_loop_v2/",
    "tests/stage1_prediction_markets/"
    "pr166_s2_replay_paper_retest_loop_v2/",
)
PR166_S2_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_s2_replay_paper_retest_loop_v2.py",
        "tools/validate_pr166_s2_replay_paper_retest_loop_v2.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_SM2_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_SM2_",
    "docs/master_plan/generated/pr166_sm2_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_sm2_score_memory_refresh_v2/",
    "tests/stage1_prediction_markets/"
    "pr166_sm2_score_memory_refresh_v2/",
)
PR166_SM2_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_sm2_score_memory_refresh_v2.py",
        "tools/validate_pr166_sm2_score_memory_refresh_v2.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
        "tests/fail_closed/test_fail_closed_guards.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_SF_R2_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_SF_R2_",
    "docs/master_plan/generated/pr166_sf_r2_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_sf_r2_targeted_conversion_repair_retest/",
    "tests/stage1_prediction_markets/"
    "pr166_sf_r2_targeted_conversion_repair_retest/",
)
PR166_SF_R2_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_sf_r2_targeted_conversion_repair_retest.py",
        "tools/validate_pr166_sf_r2_targeted_conversion_repair_retest.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/io.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_SM3_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_SM3_",
    "docs/master_plan/generated/pr166_sm3_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_sm3_score_memory_refresh_v3/",
    "tests/stage1_prediction_markets/"
    "pr166_sm3_score_memory_refresh_v3/",
)
PR166_SM3_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_sm3_score_memory_refresh_v3.py",
        "tools/validate_pr166_sm3_score_memory_refresh_v3.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/io.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_Q_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_Q_",
    "docs/master_plan/generated/pr166_q_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_q_quantum_classical_hybrid_comparator/",
    "tests/stage1_prediction_markets/"
    "pr166_q_quantum_classical_hybrid_comparator/",
)
PR166_Q_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_q_quantum_classical_hybrid_comparator.py",
        "tools/validate_pr166_q_quantum_classical_hybrid_comparator.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_QB_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_QB_",
    "docs/master_plan/generated/pr166_qb_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_qb_bounded_quantum_benchmark/",
    "tests/stage1_prediction_markets/"
    "pr166_qb_bounded_quantum_benchmark/",
)
PR166_QB_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_qb_bounded_quantum_benchmark.py",
        "tools/validate_pr166_qb_bounded_quantum_benchmark.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR166_QC_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR166_QC_",
    "docs/master_plan/generated/pr166_qc_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr166_qc_quantum_selected_replay_paper_retest/",
    "tests/stage1_prediction_markets/"
    "pr166_qc_quantum_selected_replay_paper_retest/",
)
PR166_QC_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr166_qc_quantum_selected_replay_paper_retest.py",
        "tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR162E_Q_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162E_Q_",
    "docs/master_plan/generated/pr162e_q_shards/",
    "src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper/",
    "tests/stage1_prediction_markets/pr162e_q_quantum_automapper/",
)
PR162E_Q_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162e_q_quantum_automapper.py",
        "tools/validate_pr162e_q_quantum_automapper.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR162E_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR162E_",
    "src/qtt/stage1_prediction_markets/pr162e_plugin_framework/",
    "src/qtt/plugins/",
    "tests/pr162e/",
)
PR162E_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr162e_plugin_framework.py",
        "tools/validate_pr162e_plugin_framework.py",
        "tools/validate_pr162e_negative_repair_factory.py",
        "tools/validate_pr162e_no_orphan_lineage.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/io.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR167_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR167_",
    "docs/master_plan/generated/pr167_shards/",
    "src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/",
    "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/",
)
PR167_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr167_open_trade_simulator_integration.py",
        "tools/validate_pr167_open_trade_simulator_integration.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validate_idempotence_runtime_containment.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR165_D2_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_D2_",
    "docs/master_plan/generated/pr165_d2_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr165_d2_score_refreshed_scenario_selection_v2/",
    "tests/stage1_prediction_markets/"
    "pr165_d2_score_refreshed_scenario_selection_v2/",
)
PR165_D2_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
        "tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR165_D3_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR165_D3_",
    "docs/master_plan/generated/pr165_d3_shards/",
    "src/qtt/stage1_prediction_markets/"
    "pr165_d3_quantum_aware_scenario_selection_v3/",
    "tests/stage1_prediction_markets/"
    "pr165_d3_quantum_aware_scenario_selection_v3/",
)
PR165_D3_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/build_pr165_d3_quantum_aware_scenario_selection_v3.py",
        "tools/validate_pr165_d3_quantum_aware_scenario_selection_v3.py",
        "tools/currentize_pr152_after_generated_artifacts.py",
        "tools/ci_branch_context.py",
        "tools/run_validation_gates.py",
        "tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        ".github/workflows/qtt_validation.yml",
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/report_writer.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/io.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/io.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/atomicrows/test_atomicrows_bundle_boundary_state_contract.py",
        "tests/atomicrows/test_atomicrows_bundle_materialization_manifest.py",
        "tests/atomicrows/test_atomicrows_sha_freeze_final_readiness_state_contract.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/"
        "test_pr166_sf_r2_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/"
        "test_pr166_sm3_idempotence.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    }
)
PR165_D2_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/io.py",
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/test_pr165_d2_idempotence.py",
        "tools/ci_branch_context.py",
        "tests/tools/test_ci_branch_context.py",
    }
)
PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_CHANGED_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/test_pr165_d3_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/"
        "test_pr165_d2_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/test_pr166_s2_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/test_pr166_sf_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_idempotence.py",
        "tools/ci_branch_context.py",
        "tools/validate_repair_pr_changed_file_scope.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
    }
)
PR159_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr159_official_source_completion_bridge.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR159R_BRANCH = "pr159r-exact-source-locator-value-unit-capture"
PR159R_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159R_",
    "docs/master_plan/generated/PR159S_",
    "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/",
    "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/",
    "src/qtt/stage1_prediction_markets/source_intelligence/schemas/",
    "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/",
    "tests/stage1_prediction_markets/source_intelligence/",
)
PR159R_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "tools/validate_pr159r_source_locator_value_capture.py",
        "tools/build_pr159s_open_intake_completion.py",
        "tools/validate_pr159s_open_intake_completion.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/__init__.py",
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/constants.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
PR159S_BRANCH = "pr159s-open-source-intelligence-candidate-completion"
PR159S_ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/master_plan/generated/PR159S_",
    "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/",
    "src/qtt/stage1_prediction_markets/source_intelligence/schemas/",
    "tests/stage1_prediction_markets/source_intelligence/",
)
PR159S_ALLOWED_CHANGED_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr159s_open_intake_completion.py",
        "tools/validate_pr159s_open_intake_completion.py",
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
        "src/qtt/stage1_prediction_markets/source_intelligence/__init__.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/constants.py",
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/constants.py",
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    }
)
# Exact engineering classification only. The inherited owner report remains
# read-only; this predicate does not establish byte custody or acceptance.
QTT_V35_PREFLIGHT_REPAIR_CHANGED_PATHS = frozenset({
    'src/qtt/agents/pr169_agent_orch1_resolvers.py',
    'src/qtt/optimization/pr168_qopt1/validator.py',
    'src/qtt/ranking/pr168_rank4/validator.py',
    'src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py',
    'src/qtt/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/formula_test_vectors.py',
    'src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/validator.py',
    'src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/io.py',
    'src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/validator.py',
    'src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge/validator.py',
    'src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/io.py',
    'src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py',
    'src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper/io.py',
    'src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper/report_writer.py',
    'src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper/validator.py',
    'src/qtt/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/io.py',
    'src/qtt/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/validator.py',
    'src/qtt/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator/io.py',
    'src/qtt/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator/validator.py',
    'src/qtt/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/io.py',
    'src/qtt/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/report_writer.py',
    'src/qtt/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/validator.py',
    'src/qtt/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/io.py',
    'src/qtt/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/report_writer.py',
    'src/qtt/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/validator.py',
    'src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/io.py',
    'src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/report_writer.py',
    'src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/validator.py',
    'src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/contextual_computability.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_policy.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/protocols.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/sqlite_reference.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/stack_resolver.py',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py',
    'src/qtt/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/compact_records.py',
    'tests/fail_closed/test_pytest_fresh_basetemp_helper.py',
    'tests/fail_closed/test_run_validation_gates.py',
    'tests/global_debug/test_grand_global_debug_logical_consistency_audit.py',
    'tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py',
    'tests/pr168_qopt1/test_qopt1_builder.py',
    'tests/pr168_rank4/test_rank4_builder.py',
    'tests/pr168_rp2/test_file_aliases.py',
    'tests/pr168_rp5a/_helpers.py',
    'tests/pr168_rp5a/test_cross_graph_consistency.py',
    'tests/pr168_rp5a/test_no_validation_scope_removal.py',
    'tests/pr168_rp5a/test_scan_is_bounded.py',
    'tests/pr168_rp5b/test_rp5a_inputs_exist.py',
    'tests/pr168_rp5d/test_rp5d_validation.py',
    'tests/pr169_agent_orch1/test_resolvers.py',
    'tests/pr169_dash1_ui1/test_ui1_generated_projections_not_manual_truth.py',
    'tests/pr169_pretrade1/test_pr169_pretrade1.py',
    'tests/pr169_readiness1/test_pr169_readiness1.py',
    'tests/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/test_pr162c_formula_implementations_have_test_vectors.py',
    'tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge/test_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py',
    'tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_generated_artifacts_are_deterministic.py',
    'tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_generated_artifacts_are_deterministic.py',
    'tests/stage1_prediction_markets/pr159_official_source_completion_bridge/test_pr159_generated_artifacts_are_deterministic.py',
    'tests/stage1_prediction_markets/pr159r_source_locator_value_capture/helpers.py',
    'tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_generated_artifacts_are_deterministic.py',
    'tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_selection_readiness_update_metadata_only.py',
    'tests/stage1_prediction_markets/pr162e_q_quantum_automapper/test_pr162e_q_artifacts.py',
    'tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/test_pr165_d3_build_outputs.py',
    'tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator/test_pr166_q_build_outputs.py',
    'tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/test_pr166_qb_artifacts.py',
    'tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_artifacts.py',
    'tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_artifacts.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/accounting/test_contract_matrix.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/security/test_input_validation.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_resolution_pipeline.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_service_operations.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/__init__.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_adversarial_matrix.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_e/test_integration_matrix.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_f/test_model_risk_llm_matrix.py',
    'tests/tools/test_currentize_pr152_after_generated_artifacts.py',
    'tests/tools/test_validate_repair_pr_changed_file_scope.py',
    'tools/build_pr168_rp5a_legacy_semantic_audit.py',
    'tools/build_pr169_dash1_owner_dashboard_ui.py',
    'tools/changed_area_validation_router.py',
    'tools/ci_branch_context.py',
    'tools/currentize_pr152_after_generated_artifacts.py',
    'tools/independent_validate_qku_computation_control_plane.py',
    'tools/independent_validate_qku_computation_control_plane_accounting.py',
    'tools/independent_validate_qku_computation_control_plane_architecture.py',
    'tools/independent_validate_qku_computation_control_plane_e.py',
    'tools/independent_validate_qku_computation_control_plane_execution.py',
    'tools/independent_validate_qku_computation_control_plane_model_risk.py',
    'tools/independent_validate_qku_computation_control_plane_quantum.py',
    'tools/pr168_rp2_reports.py',
    'tools/pr168_rp5a_agent_touchpoints.py',
    'tools/pr168_rp5a_git_grep_scanner.py',
    'tools/pr168_rp5a_identity_dependency.py',
    'tools/pr168_rp5a_json_scanner.py',
    'tools/pr168_rp5a_row_field_hit_index.py',
    'tools/pr168_rp5a_term_taxonomy.py',
    'tools/pr168_rp5a_validation_dependency_graph.py',
    'tools/pr168_rp5a_validator.py',
    'tools/pr168_rp5b_rp5a_loader.py',
    'tools/pr168_rp5b_validator.py',
    'tools/run_pytest_fresh_basetemp.py',
    'tools/run_validation_gates.py',
    'tools/validate_pr162e_q_quantum_automapper.py',
    'tools/validate_pr166_qb_bounded_quantum_benchmark.py',
    'tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py',
    'tools/validate_pr168_rp5a_legacy_semantic_audit.py',
    'tools/validate_pr169_pretrade1.py',
    'tools/validate_pr169_readiness1.py',
    'tools/validate_repair_pr_changed_file_scope.py',
    'tools/validation_reliability.py',
    '.github/workflows/qtt_validation.yml',
    'src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py',
    'tools/validate_no_runtime_artifacts.py',
    'tests/fail_closed/test_no_runtime_artifacts_strict.py',
    'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_h/test_contract_matrix.py',
    'tools/validate_nested_validator_contracts.py',
    'tools/validation_inventory.py',
    'tools/cross_platform_path_invariant.py',
    'tests/tools/test_ci_branch_context.py',
    'tests/tools/test_changed_area_validation_router.py',
    'tests/tools/test_cross_platform_path_invariant.py',
    'tests/tools/test_validation_inventory.py',
    'src/qtt/stage1_prediction_markets/qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py',
    'tools/validation_scope_registry.py',
    'tools/validate_grand_global_debug_logical_consistency_audit.py',
    'tools/validate_ci_branch_context_matrix.py',
    'tools/validate_validation_inventory.py',
    'tools/validate_validation_scope_registry.py',
})

EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS = {
    'repair/main-cumulative-v35-final-r5-local-20260922': QTT_V35_PREFLIGHT_REPAIR_CHANGED_PATHS,
    ENGVR_IMPLEMENTATION_BRANCH: ENGVR_CHANGED_PATHS,
    ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH: (
        ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_CHANGED_PATHS
    ),
    ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH: (
        ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_CHANGED_PATHS
    ),
    NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_BRANCH: (
        NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_CHANGED_PATHS
    ),
    PR152_HELPER_CLI_TEMP_REPO_GIT_STATUS_REPAIR_BRANCH: frozenset(
        {
            ".github/workflows/qtt_validation.yml",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/source_evidence/test_pr123_pr106_preserves_run_validation_gates_fresh_tempdir.py",
            "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
            "tests/tools/test_changed_area_validation_router.py",
            "tests/tools/test_ci_branch_context.py",
            "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
            "tests/tools/test_validate_idempotence_runtime_containment.py",
            "tests/tools/test_validation_inventory.py",
            "tools/changed_area_validation_router.py",
            "tools/ci_branch_context.py",
            "tools/currentize_pr152_after_generated_artifacts.py",
            "tools/run_validation_gates.py",
            "tools/validate_idempotence_runtime_containment.py",
            "tools/validation_inventory.py",
        }
    ),
    PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH: (
        PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_CHANGED_PATHS
    ),
    PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH: frozenset(
        {
            "tools/ci_branch_context.py",
            "tests/tools/test_ci_branch_context.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "src/qtt/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/validator.py",
            "tests/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/"
            "test_pr159r_branch_context_relaxation.py",
            "src/qtt/stage1_prediction_markets/"
            "source_intelligence/pr159s_open_intake/validator.py",
            "tests/stage1_prediction_markets/"
            "source_intelligence/test_pr159s_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/validator.py",
            "tests/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/"
            "test_pr160_branch_context_relaxation.py",
            "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "pr161a_materialization_bridge/validator.py",
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "test_pr161a_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/validator.py",
            "tests/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/"
            "test_pr161b_branch_context.py",
            "src/qtt/stage1_prediction_markets/"
            "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
            "validator.py",
            "src/qtt/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
            "tests/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/"
            "test_pr163_c_repeat_run_determinism.py",
        }
    ),
    "repair-pr153r-redo-report-determinism": frozenset(
        {
            "tools/ci_branch_context.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        }
    ),
    "repair/pr153s-source-value-capture-closure-classifier": frozenset(
        {
            "docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/__init__.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/classifier.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/inputs.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/report.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/taxonomy.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/validator.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/source_evidence/test_pr153s_source_value_capture_closure_classifier.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr153s_source_value_capture_closure_classifier.py",
        }
    ),
    "repair/pr154-post-merge-pytest-context-hygiene": frozenset(
        {
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
        }
    ),
    "pr154-atomicrows-parameter-default-value-materialization-gate": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/__init__.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/inputs.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/materializer.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/report.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/taxonomy.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/validator.py",
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_atomicrows_parameter_default_value_materialization_gate.py",
        }
    ),
    "pr155-agent-consumable-parameter-default-registry": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json",
            "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.report.json",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/__init__.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/builder.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/constants.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/input_discovery.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/io.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/mapper.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/models.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/report.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/schema_projection.py",
            "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/validator.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_agent_consumable_parameter_default_registry.py",
        }
    ),
    "pr156-agent-default-binding-universal-intake-gate": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.registry.json",
            "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.report.json",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/__init__.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/agent_binding.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/atomicrows_ingestion.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/builder.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/classical_quantum_applicability.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/constants.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/future_routing.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/input_discovery.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/intake_templates.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/io.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/models.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/population_router.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/report.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/schema_projection.py",
            "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/validator.py",
            "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate/test_agent_default_binding_universal_intake_gate.py",
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_agent_default_binding_universal_intake_gate.py",
        }
    ),
    "pr157-pr154-atomicrows-fillpath-owner-agent-bridge": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.report.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.registry.json",
            "docs/master_plan/generated/PR157_OwnerCompletionInputRequest.packet.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0001.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0002.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0003.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0004.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0005.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0006.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0007.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0008.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0009.json",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/__init__.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/agent_responsibility_bridge.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_4183_completion.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_fill_path.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/atomicrows_source_requirement_classification.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/completion_registry.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/constants.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/input_discovery.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/io.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/models.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_editability.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_input_request.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/owner_input_validator.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/pr154_completion.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/report.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/source_authority_state.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/split_reclassification.py",
            "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/validator.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_agent_responsibility_does_not_invent_exact_agent_ids.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_4183_universe_reconciles.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_classification_counts_sum_to_4183.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_no_placeholder_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_atomicrows_source_requirement_classification_exactly_one_primary.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_classical_quantum_hybrid_metadata_only.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_constants_centralize_blockers_and_authority_profiles.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_fill_paths_have_exact_steps_acceptance_criteria_and_unblock_validator.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_generated_artifacts_are_deterministic.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_mandatory_orchestration_inputs_consumed.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/"
            "test_pr157_no_atomicrows_bundle_check"
            "sum_hash_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_orphan_status_for_all_targets_and_rows.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/"
            "test_pr157_no_qtt_check"
            "sum_freeze_global_"
            "digest_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_runtime_live_connector_replay_paper_scoring_optimizer_quantum_profit_authority.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_no_scattered_hardcoded_no_authority_vocabulary.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_orphan_count_zero.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editability_classification_for_all_targets_and_rows.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_changes_do_not_mutate_open_orders_or_positions.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_changes_route_to_replay_paper_and_block_live.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_editable_external_facts_forbidden.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_input_request_packet_generated.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_absent_does_not_fabricate_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_validator_rejects_ambiguous_or_external_fact_values.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_pr154_count_invariants.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_private_doc_requires_attestation.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_public_external_requires_existing_source_evidence.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_public_external_subpartition_invariant.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_retry_records_do_not_execute_future_source_retry_scope.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_run_validation_gates_includes_pr157.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_split_reclassification_requires_basis.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_unresolved_atomicrows_fields_have_fill_path.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_unresolved_items_have_exact_next_action.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_support.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
        }
    ),
    "pr158-owner-response-atomicrows-selection-readiness-bridge": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.registry.json",
            "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
            "docs/master_plan/generated/PR157_OwnerCompletionInputRequest.packet.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
            "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.report.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0001.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0002.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0003.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0004.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0005.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0006.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0007.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0008.json",
            "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0009.json",
            "docs/master_plan/generated/PR158_AgentAssignmentCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_AgentAssignmentCandidateMap.report.json",
            "docs/master_plan/generated/PR158_AgentFormulaAlgorithmSelectionCompatibilityMap.registry.json",
            "docs/master_plan/generated/PR158_AgentFormulaAlgorithmSelectionCompatibilityMap.report.json",
            "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.registry.json",
            "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.report.json",
            "docs/master_plan/generated/PR158_FutureResearchAdditionIntakeCompatibility.report.json",
            "docs/master_plan/generated/PR158_MasterPlanOwnerResponseSelectionReadinessBridge.registry.json",
            "docs/master_plan/generated/PR158_MasterPlanOwnerResponseSelectionReadinessBridge.report.json",
            "docs/master_plan/generated/PR158_OwnerDecisionSummaryForReview.md",
            "docs/master_plan/generated/PR158_OwnerPolicyDefaultCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_OwnerPolicyDefaultCandidateMap.report.json",
            "docs/master_plan/generated/PR158_OwnerResponseMaterializationPreview.report.json",
            "docs/master_plan/generated/PR158_PR154OwnerRouteCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_PR154OwnerRouteCandidateMap.report.json",
            "docs/master_plan/generated/PR158_PR154SplitReclassificationCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_PR154SplitReclassificationCandidateMap.report.json",
            "docs/master_plan/generated/PR158_ParameterRangeOwnerPolicyCandidateMap.registry.json",
            "docs/master_plan/generated/PR158_ParameterRangeOwnerPolicyCandidateMap.report.json",
            "docs/master_plan/generated/PR158_PrecomputedLowLatencySelectionReadinessIndex.report.json",
            "docs/master_plan/generated/PR158_PrivateDocAttestationOwnerReview.md",
            "docs/master_plan/generated/PR158_TradeContextScoringFeatureMap.report.json",
            "docs/master_plan/owner_inputs/PR157_OwnerCompletionInputResponse.json",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/__init__.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/atomicrows_selection_readiness_overlay.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/constants.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/future_research_addition_intake.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/input_discovery.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/io.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_a_agent_assignment.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_b_owner_policy_default.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_c_parameter_range_owner_policy.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_d_pr154_owner_route.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_e_split_reclassification.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/lane_f_private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/low_latency_precomputed_index.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/master_plan_authority.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/models.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/orchestration_preflight.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_decision_summary.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_response_builder.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/owner_response_validator.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/prior_artifact_reconciliation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/private_doc_attestation.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/registry.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/report.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/scoring_ranking_readiness.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/trade_context_selection_readiness.py",
            "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/validator.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_atomicrows_selection_readiness_overlay_count_4183.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_atomicrows_semantic_contract_compatibility_preserved.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_constants_centralize_blockers_and_authority_profiles.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_future_research_addition_intake_compatibility.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_generated_artifacts_are_deterministic.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_agent_assignment_uses_prior_artifacts.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_defer_exact_agent_id_to_pr163_when_ambiguous.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_a_exact_agent_ids_only_when_uniquely_supported.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_b_conservative_policy_defaults_replay_paper_required.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_b_owner_policy_defaults_use_prior_artifacts_first.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_count_invariants.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_c_no_fake_numeric_ranges.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_c_parameter_ranges_use_prior_artifacts_first.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_d_pr154_owner_routes_internal_metadata_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_e_ambiguous_records_route_to_pr160.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_e_split_reclassification_deterministic_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_f_private_doc_requires_owner_attestation.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_lane_f_raw_secret_capture_forbidden.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_low_latency_precomputed_index_static_metadata_only.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_mandatory_orchestration_inputs_consumed.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_master_plan_consumed_not_edited.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/"
            "test_pr158_no_atomicrows_bundle_check"
            "sum_hash_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_fake_owner_response_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_external_facts.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_invented_numeric_ranges.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_orphans.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_placeholder_values.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/"
            "test_pr158_no_qtt_check"
            "sum_freeze_global_"
            "digest_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_execution_authority.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_scattered_hardcoded_no_authority_vocabulary.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_changes_route_to_replay_paper_and_block_live.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_decision_summary_is_human_readable.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_editability_lifecycle_preserved.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_owner_response_items_map_to_request_ids.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_pr157_owner_request_packet_count_invariant.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_quantum_metadata_only_no_backend_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_run_validation_gates_includes_pr158.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_scoring_ranking_readiness_no_scoring_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_selection_readiness_overlay_has_scoring_feature_roles.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_source_evidence_packet_consumed.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_source_required_records_route_to_pr159.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_trade_context_selection_readiness_no_selection_execution.py",
            "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/pr158_test_support.py",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_absent_does_not_fabricate_values.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr158_owner_response_selection_readiness_bridge.py",
        }
    ),
}

GitStdout = Callable[[pathlib.Path, Sequence[str]], tuple[int, str, str]]


@dataclass(frozen=True)
class BranchContext:
    branch: str
    source: str
    git_error: str = ""


@dataclass(frozen=True)
class UpstreamBranchGatePolicy:
    gate_id: str
    upstream_pr: int
    allowed_branches: frozenset[str]
    local_repair_branches_requiring_ancestry: frozenset[str]
    detached_head_ref_branches: frozenset[str]
    main_push_allowed: bool = True


PR162_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR162_BRANCH,
        PR162A_BRANCH,
        PR162B_BRANCH,
        PR162C_BRANCH,
        PR162D_BRANCH,
        PR162D_R1_BRANCH,
        PR162R_A_BRANCH,
        PR162D_R2A_BRANCH,
        PR162R_BRANCH,
        PR162R_B_BRANCH,
        PR163_BRANCH,
        PR163_B_BRANCH,
        PR163_C_BRANCH,
        PR164_BRANCH,
        PR165_BRANCH,
        PR165_B_BRANCH,
        PR165_C_BRANCH,
        PR165_D_BRANCH,
        PR165_D2_BRANCH,
        PR166_S2_BRANCH,
        PR166_SM2_BRANCH,
        PR166_SF_R2_BRANCH,
        PR166_SM3_BRANCH,
        PR166_Q_BRANCH,
        PR166_QB_BRANCH,
        PR166_QC_BRANCH,
        PR162E_Q_BRANCH,
        PR162E_BRANCH,
        PR167_BRANCH,
        PR165_D3_BRANCH,
        PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH,
    }
)
PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161C_BRANCH,
        PR161D_BRANCH,
        PR161E_BRANCH,
        PR161F_BRANCH,
        *PR162_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161B_BRANCH,
        *PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES = frozenset(
    {
        PR161A_BRANCH,
        *PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
    }
)
PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY = frozenset(
    {
        PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
        PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
    }
)
PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY = frozenset(
    {
        PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH,
    }
)
PR159R_DETACHED_HEAD_REPAIR_BRANCHES = frozenset(
    {
        *PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        "repair/main-cumulative-v35-final-r5-local-20260922",
    }
)
PR160_DETACHED_HEAD_REPAIR_BRANCHES = frozenset(
    {
        *PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
        "repair/main-cumulative-v35-final-r5-local-20260922",
    }
)
BRANCH_CONTEXT_GATE_POLICIES = {
    "PR159R": UpstreamBranchGatePolicy(
        gate_id="PR159R",
        upstream_pr=159,
        allowed_branches=frozenset(
            {
                PR159R_BRANCH,
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=(
            PR159R_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY
        ),
        detached_head_ref_branches=PR159R_DETACHED_HEAD_REPAIR_BRANCHES,
    ),
    "PR159S": UpstreamBranchGatePolicy(
        gate_id="PR159S",
        upstream_pr=159,
        allowed_branches=frozenset(
            {
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(
            {PR159S_BRANCH_CONTEXT_REPAIR_BRANCH}
        ),
        detached_head_ref_branches=frozenset(
            {
                PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR160": UpstreamBranchGatePolicy(
        gate_id="PR160",
        upstream_pr=160,
        allowed_branches=frozenset(
            {
                PR160_BRANCH,
                PR159R_BRANCH,
                PR159S_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161A_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=(
            PR160_LOCAL_REPAIR_BRANCHES_REQUIRING_ANCESTRY
        ),
        detached_head_ref_branches=PR160_DETACHED_HEAD_REPAIR_BRANCHES,
    ),
    "PR161A": UpstreamBranchGatePolicy(
        gate_id="PR161A",
        upstream_pr=161,
        allowed_branches=frozenset(
            {
                PR161A_BRANCH,
                PR161A_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161B_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(
            {
                PR161A_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR161B": UpstreamBranchGatePolicy(
        gate_id="PR161B",
        upstream_pr=161,
        allowed_branches=frozenset(
            {
                PR161B_BRANCH,
                PR161B_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                *PR161C_THROUGH_PR164_BRANCH_CONTEXT_BRANCHES,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(
            {
                PR161B_REPAIR_BRANCH,
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            }
        ),
    ),
    "PR162A": UpstreamBranchGatePolicy(
        gate_id="PR162A",
        upstream_pr=162,
        allowed_branches=frozenset(
            {
                PR162A_BRANCH,
                PR162B_BRANCH,
                PR162C_BRANCH,
                PR162D_BRANCH,
                PR162D_R1_BRANCH,
                PR162R_A_BRANCH,
                PR162D_R2A_BRANCH,
                PR162R_BRANCH,
                PR162R_B_BRANCH,
                PR163_BRANCH,
                PR163_B_BRANCH,
                PR163_C_BRANCH,
                PR164_BRANCH,
            }
        ),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(),
    ),
    "PR163-C": UpstreamBranchGatePolicy(
        gate_id="PR163-C",
        upstream_pr=163,
        allowed_branches=frozenset({PR163_C_BRANCH}),
        local_repair_branches_requiring_ancestry=frozenset(),
        detached_head_ref_branches=frozenset(),
    ),
}


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    from tools.validation_reliability import _preflight_active_v1
    if _preflight_active_v1(repo_root) is not None:
        completed = _run_validation_scope_read(repo_root, args)
        return completed.returncode, completed.stdout, completed.stderr
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    if branch.startswith("refs/pull/"):
        return ""
    if re.match(r"^[0-9]+/(head|merge)$", branch):
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def current_branch_context(
    repo_root: pathlib.Path,
    env_candidates: Sequence[str] = BRANCH_CONTEXT_ENV_CANDIDATES,
    *,
    git_stdout: GitStdout | None = None,
) -> BranchContext:
    git_stdout = git_stdout or _git_stdout
    for env_name in env_candidates:
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return BranchContext(branch=branch, source=env_name)

    git_errors: list[str] = []
    for args in (["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]):
        branch_rc, branch_stdout, branch_err = git_stdout(repo_root, args)
        if branch_rc != 0:
            git_errors.append(branch_err or f"git {' '.join(args)} failed")
            continue
        branch = normalize_branch_context(branch_stdout)
        if branch:
            return BranchContext(branch=branch, source=f"git {' '.join(args)}")

    return BranchContext(branch="", source="", git_error="; ".join(git_errors))


def github_actions_branch_context() -> str:
    if github_actions_active() and os.getenv("GITHUB_EVENT_NAME") == "pull_request":
        return github_actions_head_ref_branch_context()
    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME", "GITHUB_REF"):
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return branch
    return ""


def github_actions_head_ref_branch_context() -> str:
    return normalize_branch_context(os.getenv("GITHUB_HEAD_REF", ""))


def github_actions_pull_request_detached_context_active(
    *,
    branch_returncode: int | None = None,
    branch: str = "",
) -> bool:
    if not github_actions_active():
        return False
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    pull_request_event = event_name in {"pull_request", "pull_request_target"}
    pull_request_ref = (
        github_ref.startswith("refs/pull/")
        or re.match(r"^[0-9]+/(head|merge)$", github_ref_name) is not None
    )
    if branch_returncode is None:
        return pull_request_event or pull_request_ref

    merge_ref = (
        re.match(r"^refs/(?:remotes/)?pull/[0-9]+/merge$", github_ref) is not None
        or re.match(r"^[0-9]+/merge$", github_ref_name) is not None
    )
    detached_branch = branch_returncode != 0 or branch.strip() in {"", "HEAD"}
    return merge_ref or (pull_request_event and detached_branch)


def github_actions_main_push_context_active() -> bool:
    if not github_actions_active():
        return False
    return (
        os.getenv("GITHUB_EVENT_NAME") == "push"
        and os.getenv("GITHUB_REF") == "refs/heads/main"
        and os.getenv("GITHUB_REF_NAME") == "main"
    )


def normalize_upstream_branch_gate(value: str | int) -> str:
    if isinstance(value, int):
        return f"PR{value}"
    gate_id = str(value).strip().upper().replace("_", "-")
    if gate_id == "PR163C":
        return "PR163-C"
    return gate_id


def upstream_branch_gate_policy(value: str | int) -> UpstreamBranchGatePolicy:
    gate_id = normalize_upstream_branch_gate(value)
    try:
        return BRANCH_CONTEXT_GATE_POLICIES[gate_id]
    except KeyError as exc:
        raise KeyError(f"unknown upstream branch gate: {value!r}") from exc


def upstream_branch_gate_pr_number(value: str | int) -> int | None:
    gate_id = normalize_upstream_branch_gate(value)
    match = re.match(r"^PR(?P<number>[0-9]+)", gate_id)
    if match is None:
        return None
    return int(match.group("number"))


def is_explicit_repair_branch_allowed_for_upstream_pr_gate(
    branch: str,
    upstream_gate: str | int,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    return (
        normalized in policy.allowed_branches
        or normalized in policy.local_repair_branches_requiring_ancestry
        or normalized in policy.detached_head_ref_branches
    )


def is_branch_allowed_for_upstream_pr_gate(
    branch: str,
    upstream_gate: str | int,
    *,
    ancestry_present: bool = False,
    include_main: bool = False,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    if (
        is_idempotence_runtime_containment_hardening_branch(normalized)
        or is_validation_infrastructure_branch(normalized)
        or is_validation_execution_branch(normalized)
        or is_owner_authorized_validation_branch(normalized)
    ):
        return True
    if normalized == "main":
        return include_main and ancestry_present
    # Local cumulative PR159R validation retains the original ancestry requirement.
    # This does not admit a detached CI context or any other upstream gate.
    if (
        policy.gate_id == "PR159R"
        and include_main is True
        and ancestry_present is True
        and is_main_cumulative_branch(normalized)
        and len(normalized) > len(MAIN_CUMULATIVE_BRANCH_PREFIX)
    ):
        return True
    if normalized in policy.allowed_branches:
        return True
    gate_pr_number = upstream_branch_gate_pr_number(upstream_gate)
    branch_pr_number = roadmap_pr_number(normalized)
    if (
        ancestry_present
        and gate_pr_number is not None
        and branch_pr_number is not None
        and branch_pr_number >= gate_pr_number
    ):
        return True
    return (
        normalized in policy.local_repair_branches_requiring_ancestry
        and ancestry_present
    )


def is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
    branch_context: str,
    upstream_gate: str | int,
) -> bool:
    normalized = normalize_branch_context(branch_context)
    if not normalized:
        return False
    policy = upstream_branch_gate_policy(upstream_gate)
    return (
        is_idempotence_runtime_containment_hardening_branch(normalized)
        or is_validation_infrastructure_branch(normalized)
        or is_validation_execution_branch(normalized)
        or is_owner_authorized_validation_branch(normalized)
        or normalized in policy.allowed_branches
        or normalized in policy.local_repair_branches_requiring_ancestry
        or normalized in policy.detached_head_ref_branches
        or (
            upstream_branch_gate_pr_number(upstream_gate) is not None
            and roadmap_pr_number(normalized) is not None
            and roadmap_pr_number(normalized)
            >= upstream_branch_gate_pr_number(upstream_gate)
        )
    )


def is_main_push_context_allowed_for_upstream_pr_gate(
    branch_context: str,
    upstream_gate: str | int,
    *,
    ancestry_present: bool,
) -> bool:
    return (
        github_actions_main_push_context_active()
        and upstream_branch_gate_policy(upstream_gate).main_push_allowed
        and normalize_branch_context(branch_context) == "main"
        and ancestry_present
    )


def changed_path_allowed_for_explicit_repair_branch(branch: str, path: str) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    return is_explicit_downstream_repair_changed_path(normalized, path)


def is_validation_infrastructure_branch(branch: str) -> bool:
    normalized = normalize_branch_context(branch)
    return normalized in VALIDATION_INFRASTRUCTURE_BRANCHES


def is_validation_execution_branch(branch: str) -> bool:
    normalized = normalize_branch_context(branch)
    return normalized in VALIDATION_EXECUTION_BRANCHES


def is_owner_authorized_validation_branch(branch: str) -> bool:
    """Recognize an exact validation-only branch without roadmap authority."""

    normalized = normalize_branch_context(branch)
    return normalized in OWNER_AUTHORIZED_VALIDATION_BRANCHES


def is_validation_infrastructure_changed_path(branch: str, path: str) -> bool:
    if not is_validation_infrastructure_branch(branch):
        return False
    normalized = path.replace("\\", "/")
    return (
        normalized in VALIDATION_INFRASTRUCTURE_CHANGED_PATHS
        or _is_pr165_scoring_changed_path(normalized)
        or _is_pr165_b_condition_memory_changed_path(normalized)
        or _is_pr165_c_memory_consumer_changed_path(normalized)
        or _is_pr165_d_scenario_selection_changed_path(normalized)
        or _is_pr165_d2_score_refreshed_selection_changed_path(normalized)
        or _is_pr165_d3_quantum_selection_changed_path(normalized)
        or _is_pr166_s_replay_paper_retest_changed_path(normalized)
        or _is_pr166_sm_score_memory_refresh_changed_path(normalized)
        or _is_pr166_sf_repair_materialization_changed_path(normalized)
        or _is_pr166_s2_replay_paper_retest_changed_path(normalized)
        or _is_pr166_sm2_score_memory_refresh_changed_path(normalized)
        or _is_pr166_sf_r2_targeted_conversion_repair_changed_path(normalized)
        or _is_pr166_sm3_score_memory_refresh_changed_path(normalized)
        or _is_pr166_q_quantum_classical_hybrid_changed_path(normalized)
        or _is_pr166_qb_bounded_quantum_benchmark_changed_path(normalized)
    )


def is_idempotence_runtime_containment_hardening_changed_path(
    branch: str,
    path: str,
) -> bool:
    normalized_path = path.replace("\\", "/")
    return (
        normalize_branch_context(branch)
        == IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_BRANCH
        and normalized_path in IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_CHANGED_PATHS
    )


def is_idempotence_runtime_containment_hardening_branch(branch: str) -> bool:
    return (
        normalize_branch_context(branch)
        == IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_BRANCH
    )


def is_repair_branch(branch: str) -> bool:
    return branch.startswith(REPAIR_BRANCH_PREFIX)


def is_main_cumulative_branch(branch: str) -> bool:
    return (
        branch == "main"
        or branch in VALIDATION_INFRASTRUCTURE_BRANCHES
        or branch.startswith(MAIN_CUMULATIVE_BRANCH_PREFIX)
    )


def roadmap_pr_number(branch: str) -> int | None:
    if normalize_branch_context(branch).startswith(PR208_CI_RUNTIME_RATIONALIZATION_BRANCH):
        return None
    match = re.match(r"^pr(?P<number>[0-9]+)[a-z]*-", branch)
    if match is None:
        return None
    return int(match.group("number"))


def is_same_pr_repair_branch(branch: str, pr_number: int) -> bool:
    if not is_repair_branch(branch):
        return False
    repair_target = branch[len(REPAIR_BRANCH_PREFIX) :]
    return roadmap_pr_number(repair_target) == pr_number


def pr_branch_ancestry_ref_candidates(branch: str) -> tuple[str, ...]:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return ()
    return (
        normalized,
        f"refs/heads/{normalized}",
        f"origin/{normalized}",
        f"refs/remotes/origin/{normalized}",
    )


def pr_branch_ancestry_present(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    for ancestor_ref in pr_branch_ancestry_ref_candidates(branch):
        ancestor_rc, _ancestor_out, _ancestor_err = git_stdout(
            repo_root,
            ["merge-base", "--is-ancestor", ancestor_ref, descendant],
        )
        if ancestor_rc == 0:
            return True
    return False


def github_merge_commit_subject_mentions_branch(subject: str, branch: str) -> bool:
    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    return (
        re.match(
            rf"^Merge pull request #[0-9]+ from [^\s/]+/{re.escape(normalized)}$",
            subject.strip(),
        )
        is not None
    )


def pr_branch_merged_ancestry_present(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    if pr_branch_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    ):
        return True

    normalized = normalize_branch_context(branch)
    if not normalized:
        return False
    log_rc, log_out, _log_err = git_stdout(
        repo_root,
        [
            "log",
            "--format=%s",
            "--fixed-strings",
            f"--grep=/{normalized}",
            descendant,
        ],
    )
    if log_rc != 0:
        return False
    return any(
        github_merge_commit_subject_mentions_branch(line, normalized)
        for line in log_out.splitlines()
    )


def _shallow_repository(
    repo_root: pathlib.Path,
    *,
    git_stdout: GitStdout,
) -> bool:
    shallow_rc, shallow_out, _shallow_err = git_stdout(
        repo_root,
        ["rev-parse", "--is-shallow-repository"],
    )
    return shallow_rc == 0 and shallow_out.strip().lower() == "true"


def _refresh_shallow_repository_history(
    repo_root: pathlib.Path,
    *,
    git_stdout: GitStdout,
) -> bool:
    fetch_attempts = (
        ["fetch", "--no-tags", "--prune", "--unshallow", "origin"],
        ["fetch", "--no-tags", "--prune", "--depth=2147483647", "origin"],
    )
    for args in fetch_attempts:
        fetch_rc, _fetch_out, _fetch_err = git_stdout(repo_root, args)
        if fetch_rc == 0:
            return True
    return False


def pr_branch_merged_ancestry_present_with_shallow_refresh(
    repo_root: pathlib.Path,
    branch: str,
    *,
    descendant: str = "HEAD",
    git_stdout: GitStdout | None = None,
) -> bool:
    git_stdout = git_stdout or _git_stdout
    if pr_branch_merged_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    ):
        return True
    if not _shallow_repository(repo_root, git_stdout=git_stdout):
        return False
    if not _refresh_shallow_repository_history(repo_root, git_stdout=git_stdout):
        return False
    return pr_branch_merged_ancestry_present(
        repo_root,
        branch,
        descendant=descendant,
        git_stdout=git_stdout,
    )


def _explicit_downstream_repair_branch_pr_number(branch: str) -> int | None:
    return EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS.get(branch)


def is_explicit_downstream_repair_branch_context_allowed(
    branch: str,
    *,
    upstream_pr: int,
) -> bool:
    normalized = normalize_branch_context(branch)
    if not is_repair_branch(normalized):
        return False
    repair_pr = _explicit_downstream_repair_branch_pr_number(normalized)
    return (
        repair_pr is not None
        and repair_pr > upstream_pr
        and (
            normalized
            in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CONTEXT_ALLOWANCES.get(
                upstream_pr,
                frozenset(),
            )
        )
    )


def is_explicit_downstream_repair_changed_path(branch: str, path: str) -> bool:
    branch = normalize_branch_context(branch)
    normalized = path.replace("\\", "/")
    if branch == ENGVR_IMPLEMENTATION_BRANCH:
        return normalized in ENGVR_CHANGED_PATHS
    exact_repair_scope = EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.get(branch)
    if is_repair_branch(branch) and exact_repair_scope is not None:
        return normalized in exact_repair_scope
    if is_idempotence_runtime_containment_hardening_changed_path(branch, normalized):
        return True
    if is_pr168_gfp_changed_path(normalized, branch):
        return True
    if (
        is_pr_or_later_branch(
            branch,
            152,
            allow_main=False,
            allow_repair=False,
        )
        and normalized in PR152_CURRENTIZATION_AFTER_FASTFAIL_MERGE_CHANGED_PATHS
    ):
        return True
    if branch == PR163_BRANCH:
        return normalized in PR163_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR163_B_BRANCH:
        return normalized in PR163_B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR163_C_BRANCH:
        return normalized in PR163_C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR163_C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR164_BRANCH:
        return normalized in PR164_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR164_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR165_BRANCH:
        return _is_pr165_scoring_changed_path(normalized)
    if branch == PR165_B_BRANCH:
        return _is_pr165_b_condition_memory_changed_path(normalized)
    if branch == PR165_C_BRANCH:
        return _is_pr165_c_memory_consumer_changed_path(normalized)
    if branch == PR165_D_BRANCH:
        return _is_pr165_d_scenario_selection_changed_path(normalized)
    if branch == PR165_D2_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH:
        return normalized in PR165_D2_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS
    if branch == PR165_D2_BRANCH:
        return _is_pr165_d2_score_refreshed_selection_changed_path(normalized)
    if branch == PR165_D3_BRANCH:
        return _is_pr165_d3_quantum_selection_changed_path(normalized)
    if branch == PR166_S_BRANCH:
        return _is_pr166_s_replay_paper_retest_changed_path(normalized)
    if branch == PR166_SM_BRANCH:
        return _is_pr166_sm_score_memory_refresh_changed_path(normalized)
    if branch == PR166_SF_BRANCH:
        return _is_pr166_sf_repair_materialization_changed_path(normalized)
    if branch == PR166_S2_BRANCH:
        return _is_pr166_s2_replay_paper_retest_changed_path(normalized)
    if branch == PR166_SM2_BRANCH:
        return _is_pr166_sm2_score_memory_refresh_changed_path(normalized)
    if branch == PR166_SF_R2_BRANCH:
        return _is_pr166_sf_r2_targeted_conversion_repair_changed_path(normalized)
    if branch == PR166_SM3_BRANCH:
        return _is_pr166_sm3_score_memory_refresh_changed_path(normalized)
    if branch == PR166_Q_BRANCH:
        return _is_pr166_q_quantum_classical_hybrid_changed_path(normalized)
    if branch == PR166_QB_BRANCH:
        return _is_pr166_qb_bounded_quantum_benchmark_changed_path(normalized)
    if branch == PR166_QC_BRANCH:
        return _is_pr166_qc_quantum_selected_replay_paper_changed_path(normalized)
    if branch == PR162E_Q_BRANCH:
        return _is_pr162e_q_quantum_automapper_changed_path(normalized)
    if branch == PR162E_BRANCH:
        return _is_pr162e_plugin_framework_changed_path(normalized)
    if branch == PR167_BRANCH:
        return _is_pr167_open_trade_simulator_changed_path(normalized)
    if branch == PR162R_B_BRANCH:
        return normalized in PR162R_B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162R_BRANCH:
        return normalized in PR162R_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_R2A_BRANCH:
        return normalized in PR162D_R2A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_R2A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162R_A_BRANCH:
        return normalized in PR162R_A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162R_A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_R1_BRANCH:
        return normalized in PR162D_R1_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_R1_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162D_BRANCH:
        return normalized in PR162D_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162D_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162C_BRANCH:
        return normalized in PR162C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162B_BRANCH:
        return normalized in PR162B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162A_BRANCH:
        return normalized in PR162A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR162_BRANCH:
        return normalized in PR162_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR162_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161F_BRANCH:
        return normalized in PR161F_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161F_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161E_BRANCH:
        return normalized in PR161E_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161E_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161D_BRANCH:
        return normalized in PR161D_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161D_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161C_BRANCH:
        return normalized in PR161C_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161C_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR159_BRANCH:
        return normalized in PR159_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR159S_BRANCH or ci_branch_context_pr159s_repair(branch):
        return normalized in PR159S_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159S_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch in {
        PR159R_BRANCH,
        PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        PR159R_DETACHED_HEAD_REPAIR_BRANCH,
    }:
        return normalized in PR159R_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR159R_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch in {
        PR160_BRANCH,
        PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH,
    }:
        return normalized in PR160_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR160_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161B_BRANCH or branch == PR161B_REPAIR_BRANCH:
        return normalized in PR161B_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161B_ALLOWED_CHANGED_PATH_PREFIXES
        )
    if branch == PR161A_BRANCH or branch == PR161A_REPAIR_BRANCH:
        return normalized in PR161A_ALLOWED_CHANGED_PATHS or any(
            normalized.startswith(prefix)
            for prefix in PR161A_ALLOWED_CHANGED_PATH_PREFIXES
        )
    return normalized in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.get(
        branch,
        frozenset(),
    )


def is_pr168_gfp_changed_path(path: str, branch: str) -> bool:
    from tools.validation_scope_registry import is_pr_scoped_changed_path_allowed

    return is_pr_scoped_changed_path_allowed(branch, path)


def _is_pr165_scoring_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_b_condition_memory_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_B_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_B_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_c_memory_consumer_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_C_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_C_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_d_scenario_selection_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_D_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_D_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_d2_score_refreshed_selection_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_D2_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_D2_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr165_d3_quantum_selection_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR165_D3_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR165_D3_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_s_replay_paper_retest_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_S_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_S_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_sm_score_memory_refresh_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_SM_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_SM_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_sf_repair_materialization_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_SF_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_SF_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_s2_replay_paper_retest_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_S2_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_S2_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_sm2_score_memory_refresh_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_SM2_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_SM2_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_sf_r2_targeted_conversion_repair_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_SF_R2_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_SF_R2_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_sm3_score_memory_refresh_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_SM3_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_SM3_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_q_quantum_classical_hybrid_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_Q_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_Q_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_qb_bounded_quantum_benchmark_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_QB_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_QB_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr166_qc_quantum_selected_replay_paper_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR166_QC_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR166_QC_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr162e_q_quantum_automapper_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR162E_Q_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR162E_Q_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr162e_plugin_framework_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR162E_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR162E_ALLOWED_CHANGED_PATH_PREFIXES
    )


def _is_pr167_open_trade_simulator_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in PR167_ALLOWED_CHANGED_PATHS or any(
        normalized.startswith(prefix)
        for prefix in PR167_ALLOWED_CHANGED_PATH_PREFIXES
    )


def ci_branch_context_pr159s_repair(branch: str) -> bool:
    return branch == PR159S_BRANCH_CONTEXT_REPAIR_BRANCH


def is_downstream_roadmap_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr > after_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number > after_pr


def is_downstream_or_main_validation_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    return (
        is_idempotence_runtime_containment_hardening_branch(branch)
        or is_validation_execution_branch(branch)
        or is_owner_authorized_validation_branch(branch)
        or is_main_cumulative_branch(branch)
        or is_downstream_roadmap_branch(
            branch,
            after_pr,
            allow_repair=allow_repair,
        )
    )


def is_pr_or_later_branch(
    branch: str,
    minimum_pr: int,
    *,
    allow_main: bool = True,
    allow_repair: bool = True,
) -> bool:
    if (
        is_idempotence_runtime_containment_hardening_branch(branch)
        or is_owner_authorized_validation_branch(branch)
    ):
        return True
    if allow_main and is_main_cumulative_branch(branch):
        return True
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr >= minimum_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number >= minimum_pr


def _run_repository_read_process(repo_root: pathlib.Path, selected: Sequence[str], *, native_query=None) -> subprocess.CompletedProcess[str]:
    from tools.validation_reliability import _preflight_active_v1, _preflight_git_process_v1, _preflight_chain_v1
    observation = _preflight_active_v1(repo_root)
    if observation is not None:
        observation.reserve("attempts")
        try:
            _preflight_chain_v1(pathlib.Path(repo_root).absolute())
        except BaseException as exc:
            observation.fail(exc)
    root_text = str(repo_root)
    if any(ord(character) < 32 or ord(character) == 127 for character in root_text):
        raise ValueError("invalid repository root text")
    root = pathlib.Path(repo_root).resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    environment: dict[str, str] = {}
    seen: set[str] = set()
    for key, value in os.environ.items():
        if (type(key) is not str or type(value) is not str or not key
                or "=" in key or "\x00" in key or "\x00" in value
                or key.upper() in seen):
            raise ValueError("invalid or case-colliding child environment")
        seen.add(key.upper())
        if not key.upper().startswith("GIT_"):
            environment[key] = value
    environment.update({
        "GIT_CEILING_DIRECTORIES": str(root.parent),
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
        "GIT_ALLOW_PROTOCOL": "", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TRACE2": "0", "GIT_TRACE2_PERF": "0", "GIT_TRACE2_EVENT": "0",
        "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "protocol.allow",
        "GIT_CONFIG_VALUE_1": "never",
    })
    from tools.validation_reliability import _linux_preflight_git_environment_v1
    environment.update(_linux_preflight_git_environment_v1(root,observation))
    prefix = ["git", "--no-pager", "--literal-pathspecs", "-c",
              "core.fsmonitor=false", "-c", "protocol.allow=never"]
    options = dict(cwd=root, env=environment, stdin=subprocess.DEVNULL,
                   shell=False, check=False, capture_output=True,
                   text=True, encoding="utf-8", errors="strict")
    if native_query is not None:
        from tools.validation_reliability import _LinuxPreflightQueriesV1
        if (type(native_query) is not _LinuxPreflightQueriesV1 or observation is not None
                or tuple(selected) != ('rev-parse','--path-format=absolute','--git-path','index')):
            raise ValueError('only the original bounded Linux active-index read is selected')
    def acquire(arguments):
        if native_query is not None:
            argv = ('/usr/bin/git',*prefix[1:],*arguments)
            raw = native_query.command(argv,cwd=root,
                git_environment={k:v for k,v in environment.items() if k.startswith('GIT_')})
            return subprocess.CompletedProcess(argv,0,raw.decode('utf-8','strict'),'')
        if observation is not None:
            return _preflight_git_process_v1(observation, tuple([*prefix, *arguments]), root=root, environment=environment)
        return subprocess.run([*prefix, *arguments], **options)
    discovery = acquire(("rev-parse", "--show-toplevel"))
    if type(discovery.returncode) is not int or discovery.returncode != 0:
        raise ValueError(f"PR152 repository discovery failed: {discovery!r}")
    discovered = discovery.stdout.removesuffix("\n").removesuffix("\r")
    if (not discovered or any(ord(character) < 32 or ord(character) == 127
                               for character in discovered)):
        raise ValueError("invalid Git repository root text")
    if pathlib.Path(discovered).resolve(strict=True) != root:
        raise ValueError("REPOSITORY_ROOT_MISMATCH")
    completed = acquire(selected)
    if type(completed.returncode) is not int:
        raise ValueError("Git read did not retain an integer native exit")
    return completed


def _run_validation_scope_read(
    repo_root: pathlib.Path, arguments: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    """Separate closed scope profile; the original PR152 profile stays closed."""
    if isinstance(arguments, (str, bytes)) or not isinstance(arguments, Sequence):
        raise ValueError("scope read arguments must be a string sequence")
    if not all(type(value) is str for value in arguments):
        raise ValueError("scope read arguments must be exact strings")
    selected = tuple(arguments)
    fixed = {
        ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"),
        ("branch", "--show-current"),
        ("rev-parse", "--abbrev-ref", "HEAD"),
    }
    refs = ()
    if selected in fixed:
        pass
    elif len(selected) == 4 and selected[:2] == ("merge-base", "--all"):
        refs = selected[2:]
    elif len(selected) == 10 and selected[:7] == (
        "diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none",
    ) and selected[-1] == "--":
        refs = selected[7:9]
    else:
        raise ValueError("unadmitted scope Git read vector")
    if any(not ref or ref.startswith("-") or any(c in ref for c in "\0\r\n") for ref in refs):
        raise ValueError("invalid exact scope comparison reference")
    return _run_repository_read_process(repo_root, selected)


def _facet_fn_source_keeper_borrow_v1(source, row, version=None, flags=None, operation='identity'):
    """Observe only the fixed Input4 keeper loan; never acquire its undo debt."""
    import select
    import tools.validation_reliability as f
    require=f._preflight_require_v1
    scope=getattr(source,'_ordinary_meter_scope_v1',None)
    if scope is None:return False
    require(type(source)is f._LinuxImmutableSourceSealV2 and scope.source is source
        and type(scope)is f._LinuxPreflightScopeV1
        and (source.pid,source.thread)==scope._ordinary_factory_owner_v1
        ==(f.os.getpid(),f.threading.get_ident()),'SOURCE_KEEPER_ORIGINAL_LOCAL_OWNER')
    native=scope._ordinary_bootstrap_runtime_v1['acquisition']['native_product']
    generation=native['source_generation'];binding=generation.get('native_input_binding')
    if binding is None:return False
    original=generation.get('keeper_borrow_original')
    require(type(binding)is dict and type(original)is tuple and len(original)==17
        and binding['original']is original and original[0]is binding
        and binding['complete']is True,'SOURCE_KEEPER_COMPLETED_ORIGINAL_REJOIN')
    fields=('generation','native_input','generation_original','inputs','rows','root_slot',
        'physical','physical_original','physical_result','cutoffs','role','producer',
        'producer_code','containing_function','containing_code','errors')
    require(all(original[i+1]is binding[name]for i,name in enumerate(fields)),
        'SOURCE_KEEPER_ORIGINAL17_FIELDS')
    ni=binding['native_input'];physical=binding['physical'];hold=native['native_hold']
    f._ordinary_initial_preloader_return_check_v1(ni)
    nf=('native_input','native_hold','native_generation','startup','source_generation','roles',
        'actor','phase','role','native_root','origin_ns','errors')
    no=native['original']
    hf=('owner','service_unit','invocation','holder_identity','holder_pidfd_slot','holder_cgroup',
        'holder_cgroup_slot','holder_events_slot','ancestor_cgroup','ancestor_slot','cutoffs','errors',
        'holder_kernel_observations','native_input','native_generation','source_generation','startup')
    ho=hold['original'];po=physical['original'];pr=physical['result_original']
    require(type(no)is tuple and len(no)==13 and no[0]is native
        and all(no[i+1]is native[name]for i,name in enumerate(nf))
        and type(ho)is tuple and len(ho)==18 and ho[0]is hold
        and all(ho[i+1]is hold[name]for i,name in enumerate(hf))
        and type(po)is tuple and len(po)==12 and all(left is right for left,right in zip(po,
            (physical,ni,physical['native'],physical['profile'],physical['operands'],
                ni['initial_operands_original'],physical['owner'],ni['errors'],physical['slots'],
                physical['reads'],physical['commands'],physical['operations'])))
        and type(pr)is tuple and len(pr)==16 and pr[0]is physical and pr[1]is po
        and pr[2]is native['actor']and pr[3]==native['origin_ns']and pr[15]is ni['errors']
        and hold['holder_pidfd_slot']is physical['holder_pidfd_slot']
        and hold['holder_events_slot']is physical['holder_events_slot']
        and hold['holder_cgroup_slot']is physical['held_cgroups']['holder_cgroup']
        and hold['ancestor_slot']is physical['held_cgroups']['ancestor_cgroup']
        and hold['holder_kernel_observations']is physical['kernel_controls'],
        'SOURCE_KEEPER_SAME_NATIVE13_HOLD18_AND_PHYSICAL12_16')
    source_original=generation['original'];producer=binding['producer'];container=binding['containing_function']
    require(binding['generation']is generation and ni is native['native_input']
        and binding['generation_original']is source_original
        and type(source_original)is tuple and len(source_original)==17
        and source_original[0]is generation and source_original[1]is ni
        and source_original[10]is generation['native_method']
        and source_original[11]is generation['native_method_code']is generation['native_method'].__code__
        and container is generation['native_method']is source_original[10]
        and f._LinuxSourceNativeV2.__dict__['_ordinary_initial_native_product_v1'].__func__ is container
        and binding['containing_code']is container.__code__ is source_original[11]
        and type(producer)is type(container)and producer.__name__=='_original_source_input4_rejoin_v1'
        and producer.__globals__ is container.__globals__ is generation['module_namespace']is f.__dict__
        and producer.__code__ is binding['producer_code']
        and any(code is producer.__code__ for code in container.__code__.co_consts)
        and physical is ni['current_native_observation']
        and physical['original']is binding['physical_original']
        and physical['result_original']is binding['physical_result']
        and physical['complete']is True and physical['pending']is False
        and physical['owner']==ni['owner']==scope._ordinary_factory_owner_v1
        and binding['errors']is ni['errors']is physical['errors']is native['errors']
        and not binding['errors'] and native['role']==binding['role']==physical['operands']['role']
        and binding['cutoffs']is hold['cutoffs']is scope._ordinary_host_preparation_v1['original_cutoffs']
        and binding['cutoffs']==(native['origin_ns'],native['origin_ns']+3500*10**9,
            native['origin_ns']+3600*10**9,native['origin_ns']+3720*10**9)
        and native['actor']is physical['actor'] and hold['holder_identity']==physical['holder'],
        'SOURCE_KEEPER_FIXED_PRODUCER_AND_ORIGINAL_LIFETIME')
    record=source._ordinary_source_meter_record_v1
    require(record['source']is source and record['parent']is None
        and source._ordinary_meter_scope_v1._ordinary_source_meter_projection_v1(source)is record,
        'SOURCE_KEEPER_ONLY_PRIMARY_SOURCE_SEAL')
    inputs=binding['inputs'];rows=binding['rows'];root=binding['root_slot']
    paths=(generation['workflow'],*generation['expected_module_closure'])
    names=('workflow','run-validation-source','reliability-source','scope-registry-source',
        'branch-context-source','inventory-source','repo-path-source','compiler-image')
    require(type(inputs)is tuple and len(inputs)==8 and generation['protected_inputs']is inputs
        and type(rows)is list and len(rows)==7 and len(paths)==7
        and type(generation['control_source_originals'])is list
        and len(generation['control_source_originals'])==4
        and all(left is right for left,right in zip(generation['control_source_originals'],(rows[i]for i in(2,1,3,5))))
        and all(type(pair)is tuple and len(pair)==2 and pair[0]==names[i]
            and type(pair[1])is tuple and len(pair[1])==4 for i,pair in enumerate(inputs)),
        'SOURCE_KEEPER_EXACT_SEVEN_SOURCE_AND_EIGHT_INPUT_ORDER')
    def held(slot,regular):
        require(type(slot)is dict and any(slot is actual for actual in physical['slots'])
            and slot['owner']==physical['owner'] and slot['held']is True
            and type(slot['returned_fd'])is int and slot['returned_fd']>=0
            and slot['open_attempted']is True and not slot['close_admission_attempted']
            and not slot['close_attempted']and not slot['closed']and not slot['errors']
            and slot['complete']is True and type(slot['flags'])is int and slot['flags']&16
            and slot['acl']==(None,None) and type(slot['version'])is list
            and len(slot['version'])==11 and all(type(n)is int for n in slot['version'])
            and slot['version9']==tuple(slot['version'][i]for i in(0,1,2,7,8,6,3,4,5))
            and slot['version'][7]==slot['version'][8]==0
            and not slot['version'][9]&0x400 and slot['version'][10]==0
            and (f.stat.S_ISREG(slot['version'][2])and slot['version'][6]==1 if regular
                else f.stat.S_ISDIR(slot['version'][2]))
            and f.stat.S_IMODE(slot['version'][2])==(0o555 if not regular or slot['version'][2]&0o111 else 0o444),
            'SOURCE_KEEPER_SAME_HELD_LOCAL_PROTECTED_OPERAND')
    held(root,False)
    require(type(root['path'])is type(f.Path('/')) and root['path'].is_absolute()
        and root['path'].name==physical['operands']['stem']+'inputs','SOURCE_KEEPER_FIXED_INPUT_ROOT')
    rb=root['source_binding_original']
    require(type(rb)is tuple and len(rb)==18 and all(left is right for left,right in zip(rb[:12],
        (root,binding,generation,source_original,ni,physical,po,pr,physical['native_root_slot'],
            physical['operands'],ni['initial_operands_original'],binding['cutoffs'])))
        and type(rb[12])is tuple and len(rb[12])==4
        and tuple(key for key,value in rb[12])==('GITHUB_WORKSPACE','RUNNER_TEMP','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT')
        and all(type(value)is str and value for key,value in rb[12])
        and rb[13]is root['version']and rb[14]is root['version9']
        and rb[15]is root['flags']and rb[16]is root['acl']and rb[17]is inputs
        and root['path']==f.Path(rb[12][1][1])/(physical['operands']['stem']+'inputs')
        and str(generation['workflow'])==rb[12][0][1]+'/.github/workflows/qtt_validation.yml',
        'SOURCE_KEEPER_ORIGINAL_SOURCE_SELECTED_PARENT_AND_ROOT18')
    for index,(_,item)in enumerate(inputs):
        require(type(item[0])is str and type(item[2])is str
            and type(item[1])is tuple and len(item[1])==9
            and type(item[3])is tuple and len(item[3])==9
            and all(type(n)is int for n in item[1]+item[3])
            and f.Path(item[2])==root['path']/('input'+str(index)),
            'SOURCE_KEEPER_ALL_EIGHT_ORIGINAL_INPUT4')
        for path,saved in ((item[0],item[1]),(item[2],item[3])):
            matches=[slot for slot in physical['slots']if slot.get('path')==f.Path(path)
                and slot.get('version9')is saved]
            require(len(matches)==1,'SOURCE_KEEPER_EXACT_LOCAL_SLOT')
            held(matches[0],True)
    require(operation in('identity','sealed','recovery','protect','release','profile','settled','journal','journal-flush'),
        'SOURCE_KEEPER_CLOSED_PRIVATE_OWNER_SEAM')
    journal=getattr(source,'_ordinary_keeper_borrow_observations_v1',None)
    if journal is None:
        journal=[];source._ordinary_keeper_borrow_observations_v1=journal
        source._ordinary_keeper_borrow_observations_original_v1=(source,binding,original,journal)
    jo=source._ordinary_keeper_borrow_observations_original_v1
    require(type(jo)is tuple and len(jo)==4 and jo[0]is source and jo[1]is binding
        and jo[2]is original and jo[3]is journal,'SOURCE_KEEPER_SAME_OBSERVATION_LIST')
    if operation=='journal':
        require(source.journal_fd is None and not hasattr(source,'_ordinary_keeper_journal_plan_v1'),
            'SOURCE_KEEPER_ONE_PROSPECTIVE_JOURNAL_PLAN')
        work=settlement=0
        for value in rows:
            key=value['filename'];i=source.journal_ids[key];flags=value['source_row']['flags']
            ordinary=dict(entry=i,operation='borrow-lifetime',result='OBSERVED',returned=[])
            failure=dict(entry=i,operation='borrow-lifetime',result='UNCERTAIN',
                returned=[[hold['holder_pidfd_slot']['returned_fd'],65535]],error='\x00'*384)
            maximum=max(len(f._preflight_canonical_v1(event))+1 for event in(ordinary,failure))
            work+=8*maximum+len(f._preflight_canonical_v1(dict(entry=i,operation='borrow-protected',
                result='OBSERVED',version=source.row_index[key]['version'],flags=flags)))+1
            settlement+=3*maximum+len(f._preflight_canonical_v1(dict(entry=i,operation='borrow-release',
                result='OBSERVED',version=source.row_index[key]['version'],flags=flags)))+1
        reservation=source.journal_reservation
        require(sum(reservation[p]['bytes']for p in('work','settlement'))+work+settlement
            +sum(case.get('evidence',{}).get('journal_bytes',0)for case in source.recovery_cases)
            <=32*1024**2,'SOURCE_KEEPER_PROSPECTIVE_JOURNAL_CAPACITY')
        reservation['work']['bytes']+=work;reservation['work']['records']+=63
        reservation['settlement']['bytes']+=settlement;reservation['settlement']['records']+=28
        source._ordinary_keeper_journal_plan_v1=(source,binding,original,reservation,tuple(journal),work,settlement)
        return True
    if operation=='journal-flush':
        plan=source._ordinary_keeper_journal_plan_v1
        require(plan[0]is source and plan[1]is binding and plan[2]is original
            and plan[3]is source.journal_reservation and source.journal_fd is not None
            and not hasattr(source,'_ordinary_keeper_journal_flush_v1'),
            'SOURCE_KEEPER_SINGLE_PREJOURNAL_OBSERVATION_FLUSH')
        source._ordinary_keeper_journal_flush_v1=plan
        for event in plan[4]:source._record(event)
        return True
    matches=[value for value in rows if value['filename']==row['path']]
    if not matches:return False
    require(len(matches)==1 and row['role']=='repository'and row['kind']=='file',
        'SOURCE_KEEPER_NO_DIRECTORY_OR_FOREIGN_BORROW')
    value=matches[0];index=next(i for i,actual in enumerate(rows)if actual is value)
    ro=value['original'];item=value['input4'];a=value['acquisition'];ao=value['acquisition_original']
    raw=value['raw'];baseline=value['baseline_raw'];sr=value['source_row'];br=value['baseline_row']
    require(type(ro)is tuple and len(ro)==10 and all(left is right for left,right in zip(ro,
        (value,generation,binding,item,sr,br,raw,baseline,a,ao)))
        and type(ao)is tuple and len(ao)==10 and all(left is right for left,right in zip(ao,
        (a,binding,value,producer,producer.__code__,sr,br,raw,baseline,binding['errors'])))
        and a['original']is ao and a['complete']is True and a['errors']is binding['errors']
        and item is inputs[index][1] and row['path']==str(paths[index])==item[0]
        and value['source_version']is item[1]is sr['version9']
        and value['baseline_version']is item[3]is br['version9']
        and row['version']==sr['version']and row['logical_bytes']==len(raw)
        and type(raw)is bytes and type(baseline)is bytes and raw==baseline
        and raw is sr['raw']and baseline is br['raw']
        and tuple(row['version'][i]for i in(0,1,2,7,8,6,3,4,5))==item[1],
        'SOURCE_KEEPER_COMPLETE_INDEPENDENT_BASELINE_AND_CENSUS')
    if operation in('identity','sealed','recovery','release'):
        require(version==row['version']and flags==sr['flags'],
            'SOURCE_KEEPER_UNCHANGED_FULL_PROTECTED_GENERATION')
    if operation in('identity','sealed','recovery','release'):
        keeper=hold['holder_pidfd_slot']
        require(keeper is physical['holder_pidfd_slot']and keeper['held']is True
            and keeper['owner']==physical['owner']and not keeper['close_attempted']
            and not keeper['closed']and not keeper['errors']
            and type(keeper['returned_fd'])is int and keeper['returned_fd']>=0,
            'SOURCE_KEEPER_ORIGINAL_OUTSIDE_PIDFD')
        event=dict(entry=source.journal_ids[row['path']],operation='borrow-lifetime',result='OBSERVED')
        errors=[]
        try:
            poll=select.poll();poll.register(keeper['returned_fd'],select.POLLIN)
            event['returned']=scope._ordinary_factory_call_v1(poll.poll,0,settling=source.phase=='settlement')
            require(type(event['returned'])is list and len(event['returned'])<=1,
                'SOURCE_KEEPER_ONE_REGISTERED_PIDFD_RESULT')
            require(not event['returned'],'SOURCE_KEEPER_OUTSIDE_CUSTODIAN_TERMINATED')
        except BaseException as error:
            event['result']='UNCERTAIN';event['error']=repr(error).encode('utf-8')[:384].decode('utf-8','replace')
            errors.append(error)
        journal.append(event)
        if source.journal_fd is not None:
            try:source._record(event)
            except BaseException as error:errors.append(error)
        for error in errors:
            if not any(error is old for old in binding['errors']):binding['errors'].append(error)
        f._scan_raise_errors(errors)
    marker=(row['path'],'borrow-protected')
    if operation=='protect':
        require(marker not in source.attempts,'SOURCE_KEEPER_SINGLE_BORROW_ADOPTION')
        source._record(dict(entry=source.journal_ids[row['path']],operation='borrow-protected',
            result='OBSERVED',version=row['version'],flags=sr['flags']))
        source.attempts.add(marker);source.post[row['path']]=row['version']
    elif operation=='release':
        require(marker in source.attempts,'SOURCE_KEEPER_ONLY_ACTUAL_BORROW_RELEASE')
        source._record(dict(entry=source.journal_ids[row['path']],operation='borrow-release',
            result='OBSERVED',version=version,flags=flags))
        source.restoration_outcomes[source.journal_ids[row['path']]]='BORROW_RELEASED_READBACK'
    elif operation in('profile','settled'):
        require(marker in source.attempts and source.post[row['path']]==row['version']
            and source.original_flags[row['path']]==sr['flags']
            and not any((row['path'],name)in source.attempts for name in('chown','chmod','set-immutable')),
            'SOURCE_KEEPER_OBSERVATION_IS_NOT_OWN_TRANSITION')
        if operation=='settled':
            require(source.restoration_outcomes[source.journal_ids[row['path']]]=='BORROW_RELEASED_READBACK'
                and any(event.get('entry')==source.journal_ids[row['path']]
                    and event.get('operation')=='borrow-release'and event.get('result')=='OBSERVED'
                    and event.get('version')==row['version']and event.get('flags')==sr['flags']
                    for event in source.journal),'SOURCE_KEEPER_TRUTHFUL_BORROW_RELEASE_JOURNAL')
    return True


def _ordinary_ci_initial_common_source_v1(extent, parent_path_count):
 if type(extent)is not int or extent<=0 or type(parent_path_count)is not int or parent_path_count<0:
  raise ValueError('ORDINARY_INITIAL_COMMON_ORIGINAL_LEXICAL_AND_PARENT_STOCK')
 def U(n,c):return 68*n+4*c
 def T(n,s):return 48*n+8*s
 def L(n,s):return 56*n+16*(s+s//8+6*n)
 initializer=5125424+21625000+U(7,7*extent)+T(1,parent_path_count)
 initializer+=6*(U(67,3*extent)+L(2,130)+T(1,65))
 initializer+=672+T(1,8)+2*T(1,9)+2*T(1,parent_path_count)+24
 return(2361360383,301158970,32860047,initializer,1802350,241543444,18356704,1814632,1980516)

def _ordinary_ci_initial_common_source_check_v1(native_input,profile,allocation):
 issue=native_input['initial_request_issuer'];source=issue['source_generation'];old=issue['common_source_original'];fn=_ordinary_ci_initial_common_source_v1
 initial=globals()['_ORDINARY_INITIALIZED_MODULE_CODE_V1']
 issued=issue['result_original'];parent_paths=old[6]
 import sys
 if(type(old)is not tuple or len(old)!=8 or old[0]is not issue or old[1]is not source or old[2]is not source['original']or old[3]is not fn or old[4]is not fn.__code__ or old[5]is not globals()or fn.__globals__ is not globals()or not any(code is fn.__code__ for code in initial.co_consts)or type(parent_paths)is not tuple or parent_paths!=tuple(sys.path)or type(old[7])is not tuple or len(old[7])!=9 or old[7]!=fn(issue['path_stock_original'][6],len(parent_paths))or issue['native_input']is not native_input or issue['complete']is not True or issue['result']is not profile or issue['allocation']is not allocation or profile is not native_input['early_profile']or allocation is not native_input['early_allocation_original']or allocation[0]is not native_input or allocation[1]is not profile or allocation[2]is not issue['limits']or type(issued)is not tuple or len(issued)!=7 or issued[0]is not issue or issued[1]is not issue['original']or issued[2]is not profile[7]or issued[2]is not issue['components']or issued[3]!=tuple(allocation[2].items())or issued[4]is not allocation or issued[5]is not allocation[3]or issued[6]is not profile or source is not native_input['source_generation']or source['original'][1]is not native_input or issue['errors']is not native_input['errors']):
  raise ValueError('ORDINARY_INITIAL_SAME_COMPLETE_COMMON_SOURCE_AND_FROZEN_ALLOCATION')
 return old[7]

def _ordinary_ci_initial_source_request_v1(native_input, source_generation,
 native_generation, startup_source, *, phase, producer):
 """Calculate the original pending bootstrap request; acquire no physical input."""
 from types import FunctionType,CodeType,ModuleType
 carriers=(native_input,source_generation,native_generation,startup_source)
 if any(type(item)is not dict for item in carriers) or type(phase)is not str or not phase:
  raise ValueError('ORDINARY_INITIAL_SOURCE_EXACT_PENDING_CARRIERS')
 entry=native_input.get('entry_original');errors=native_input.get('errors')
 if (type(entry)is not tuple or len(entry)!=9 or type(errors)is not list or errors
  or type(entry[0])is not dict or entry[0]is not native_input.get('entry_attempt')
  or entry[0].get('native_input')is not native_input or entry[2]is not errors
  or entry[3]is not phase or native_input.get('owner')is not entry[1]
  or type(entry[4])is not ModuleType or type(entry[5])is not dict
  or entry[5]is not entry[4].__dict__ or type(entry[6])is not CodeType
  or type(entry[7])is not FunctionType or entry[8]is not entry[7].__code__
  or type(producer)is not FunctionType or producer.__globals__ is not entry[5]
  or entry[5].get('_ordinary_bootstrap_initial_source_request_v1')is not producer
  or producer.__defaults__ is not None or producer.__kwdefaults__ is not None
  or producer.__closure__ is not None):
  raise ValueError('ORDINARY_INITIAL_SOURCE_ORIGINAL_RUN_EMITTER')
 if native_input.get('initial_request_issuer')is not None:
  raise ValueError('ORDINARY_INITIAL_SOURCE_REQUEST_ONE_ORIGINAL_ATTEMPT')
 issue=dict(native_input=native_input,source_generation=source_generation,
  native_generation=native_generation,startup_source=startup_source,
  phase=phase,producer=producer,producer_code=producer.__code__,errors=errors,
  components=None,limits=None,allocation=None,result=None,complete=False)
 native_input['initial_request_issuer']=issue
 issue['original']=(issue,native_input,source_generation,native_generation,
  startup_source,phase,producer,producer.__code__,entry,errors)
 try:
  source=source_generation.get('original');native=native_generation.get('original')
  startup=startup_source.get('original');programme=native_input.get('preloader_programme_original')
  origin=native_input.get('original_origin_request')
  if (type(source)is not tuple or len(source)!=17 or source[0]is not source_generation
   or source[1]is not native_input or source[2]is not entry
   or source[3]is not entry[4] or source[4]is not entry[5] or source[5]is not entry[6]
   or source[6]is not entry[7] or source[7]is not entry[8]
   or type(source[8])is not ModuleType or source[9]is not source[8].__dict__
   or source[16]is not errors or type(native)is not tuple or len(native)!=10
   or native[0]is not native_generation or native[1]is not native_input
   or native[2]is not source_generation or native[-1]is not errors
   or type(startup)is not tuple or len(startup)!=12 or startup[0]is not startup_source
   or startup[1]is not native_input or startup[2]is not source_generation
   or startup[-1]is not errors or type(programme)is not tuple or len(programme)!=23
   or programme[1]is not native_input or programme[2]is not entry
   or programme[3]is not source_generation or programme[4]is not native_generation
   or programme[5]is not startup_source or programme[22]is not errors
   or type(origin)is not dict or origin.get('source_generation')is not source_generation
   or type(origin.get('original'))is not tuple or len(origin['original'])!=15
   or origin['original'][0]is not origin or origin['original'][1]is not native_input
   or origin.get('origin_ns')is not None or origin.get('deadline_ns')is not None):
   raise ValueError('ORDINARY_INITIAL_SOURCE_SAME_PENDING_PROGRAMME_AND_ORIGIN')
  frozen=(source_generation,native_input,entry,entry[4],entry[5],entry[6],
   entry[7],entry[8],source_generation['module'],source_generation['module_namespace'],
   source_generation['native_method'],source_generation['native_method_code'],
   source_generation['code_paths'],source_generation['workflow'],
   source_generation['expected_module_closure'],source_generation['physical_observations'],errors)
  if (not all(a is b for a,b in zip(source,frozen))
   or not all(a is b for a,b in zip(native,(native_generation,native_input,
    source_generation,native_generation['native_class'],native_generation['constructor'],
    native_generation['constructor_code'],native_generation['native_method'],
    native_generation['native_method_code'],native_generation['physical_observations'],errors)))
   or not all(a is b for a,b in zip(startup,(startup_source,native_input,
    source_generation,native_generation,phase,startup_source['code_paths'],
    startup_source['workflow'],startup_source['expected_startup_keys'],
    startup_source['expected_basis_keys'],startup_source['expected_roles'],
    startup_source['physical_observations'],errors)))):
   raise ValueError('ORDINARY_INITIAL_SOURCE_UNCHANGED_ORIGINAL_CARRIER_FIELDS')
  components,limits=_ordinary_ci_initial_direct_request_v1(source[8],source_generation)
  issue['components']=components;issue['limits']=limits
  import sys
  parent_paths=tuple(sys.path);common_fn=_ordinary_ci_initial_common_source_v1
  common_source=common_fn(issue['path_stock_original'][6],len(parent_paths))
  issue['common_source_original']=(issue,source_generation,source,common_fn,common_fn.__code__,common_fn.__globals__,parent_paths,common_source)
  result=(native_input,source_generation,native_generation,startup_source,phase,
   origin,None,components,limits['work_calls']+limits['settlement_calls'],
   limits['work_bytes']+limits['settlement_bytes'],producer,producer.__code__)
  counters={name:0 for name in limits}
  allocation=(native_input,result,limits,counters)
  issue['allocation']=allocation;issue['result']=result
  issue['result_original']=(issue,issue['original'],components,
   tuple(limits.items()),allocation,counters,result)
  native_input['early_profile']=result
  native_input['early_allocation_original']=allocation
  issue['complete']=True
  return result
 except BaseException as error:
  if not any(error is old for old in errors):errors.append(error)
  raise


def _ordinary_ci_initial_loan_retirement_v1(native_input, scope=None, terminal=None):
 """One-close original local loans after the original terminal owner's last effect."""
 import tools.validation_reliability as _f
 prefix=_f._ordinary_initial_prefix_v1(native_input)
 prebind=native_input['origin_prebind'];original=prebind['original'];result=prebind['result_original']
 errors=native_input['errors'];owner=native_input['owner']
 _f._preflight_require_v1(prebind['complete']is True and result is native_input['origin_prebind_result_original']
  and result[0]is prebind and result[1]is original and original[1]is native_input
  and original[6]is prefix['prefix_original'] and original[7]is owner and original[8]is errors
  and prebind['slots']is original[14] and prebind['operations']is prefix['operations']
  and 'retirement' not in prebind and owner==(_f.os.getpid(),_f.threading.get_ident()),
  'ORDINARY_INITIAL_ORIGINAL_LOAN_RETIREMENT_ONE_OWNER')
 caller=_f.sys._getframe(2)
 try:
  runner=native_input['entry_original'][4]
  physical=native_input.get('current_native_observation')
  if scope is None:
   _f._preflight_require_v1(terminal is None and physical is None and errors
    and caller.f_globals is _f.__dict__ and caller.f_code in (
     _f._ordinary_initial_native_object_v1.__code__,_f._ordinary_initial_native_initialize_v1.__code__)
    and caller.f_locals.get('native_input')is native_input,
    'ORDINARY_INITIAL_COLD_FAILURE_PROVES_NO_NATIVE_DISPATCH')
  else:
   _f._preflight_require_v1(type(scope)is _f._LinuxPreflightScopeV1
    and type(physical)is dict and physical['native_input']is native_input
    and physical['complete']is True and physical['pending']is False
    and scope._ordinary_initial_native_holder_v1['native_input']is native_input
    and caller.f_globals is runner.__dict__ and caller.f_locals.get('scope')is scope
    and all(not command['pending'] and command['associated']
     and type(command['receipt'])is _f.CommandExecutionReceiptV1
     and not _f._command_requires_process_retention_v1(command['receipt'])
     for command in physical['commands']),
    'ORDINARY_INITIAL_ACTUAL_TERMINAL_SCOPE_AND_ORIGINAL_COMMANDS')
   if prebind['role']=='PARENT':
    _f._preflight_require_v1(caller.f_code is runner._ordinary_parent_durable_finish_v1.__code__
     and terminal is caller.f_locals['cleanup'] and terminal is not None
     and caller.f_locals['record']is scope._ordinary_parent_factory_v1
     and scope._ordinary_parent_factory_v1['cleanup']is terminal,
     'ORDINARY_INITIAL_PARENT_ACTUAL_UNMOUNT_FINISHED_BEFORE_LOAN_RELEASE')
   elif prebind['role']=='RECEIVER':
    _f._preflight_require_v1(caller.f_code is runner._ordinary_received_controller_durable_finish_v1.__code__
     and terminal is caller.f_locals['cleanup']is scope._ordinary_controller_run_v1['cleanup']
     and terminal['image_disposed'] and scope._ordinary_controller_run_v1['export']['closed'],
     'ORDINARY_INITIAL_RECEIVED_ACTUAL_RESTORE_EXPORT_AND_PREFIX_FINISH')
   else:
    value=caller.f_locals.get('value');observation=caller.f_locals.get('observation')
    _f._preflight_require_v1(prebind['role']=='PROVISION'
     and caller.f_code is runner._ordinary_linux_provision_v1.__code__
     and type(value)is dict and value['pid']==_f.os.getpid()
     and value['uid']==_f.os.geteuid() and value['origin_ns']==prebind['origin_ns']
     and scope is caller.f_locals['scope'] and scope._ordinary_host_preparation_v1 is caller.f_locals['host']
     and caller.f_locals['task']is physical['operands']['native_root']
     and terminal is caller.f_locals.get('receipt')
     and type(terminal)is _f.CommandExecutionReceiptV1
     and not _f._command_requires_process_retention_v1(terminal)
     and type(observation)is dict and terminal.output_observation==observation
     and all(type(observation.get(name))is dict
      and observation[name].get('complete')is True and observation[name].get('overflow')is False
      and not observation[name].get('errors')
      and observation[name]['drained_byte_count']==observation[name]['retained_byte_count']
       ==getattr(terminal,name+'_byte_count')for name in('stdout','stderr')),
     'ORDINARY_INITIAL_PROVISION_LOCAL_LOANS_AFTER_ACTUAL_PARENT_TERMINAL_EOF')
  retirement=dict(native_input=native_input,prebind=prebind,physical=physical,scope=scope,
   terminal=terminal,caller=caller.f_code,owner=owner,errors=errors,slots=prebind['slots'],
   physical_slots=None if physical is None else physical['slots'],close_records=[],complete=False)
  prebind['retirement']=retirement
  retirement['original']=(retirement,native_input,prebind,result,physical,scope,terminal,
   caller.f_code,owner,errors,retirement['slots'],retirement['physical_slots'],retirement['close_records'])
 finally:
  del caller
 for original_slots in (retirement['slots'],retirement['physical_slots']):
  if original_slots is None:continue
  for slot in reversed(original_slots):
   if slot['closed']:continue
   fd=slot['returned_fd']
   if fd is None:continue
   close_record=dict(slot=slot,fd=fd,admission_attempted=False,close_attempted=False,
    closed=False,metadata=None,error=None)
   retirement['close_records'].append(close_record)
   try:
    _f._preflight_require_v1(slot['owner']is owner and type(fd)is int and fd>=0
     and not slot['close_admission_attempted'] and not slot['close_attempted'],
     'ORDINARY_INITIAL_ORIGINAL_UNRETIRED_DESCRIPTOR')
    _f._ordinary_initial_native_debit_v1(native_input,'LOAN_RETIREMENT_METADATA',settling=True)
    info=_f.os.fstat(fd);close_record['metadata']=_f._preflight_stamp_v1(info)
    _f._preflight_require_v1((info.st_dev,info.st_ino,info.st_mode)==slot['handle_version'][:3],
     'ORDINARY_INITIAL_RETIRE_ONLY_SAME_ORIGINAL_PHYSICAL_DESCRIPTOR')
    _f._ordinary_initial_native_debit_v1(native_input,'LOAN_RETIREMENT_INHERITANCE',settling=True)
    _f._preflight_require_v1(not _f.os.get_inheritable(fd),'ORDINARY_INITIAL_RETIREMENT_NONINHERITED')
    slot['close_admission_attempted']=close_record['admission_attempted']=True
    _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True)
    slot['close_attempted']=close_record['close_attempted']=True
    _f.os.close(fd)
    slot['closed']=close_record['closed']=True
   except BaseException as error:
    close_record['error']=error
    if not any(error is old for old in slot['errors']):slot['errors'].append(error)
    if not any(error is old for old in errors):errors.append(error)
 retirement['complete']=all(slot['returned_fd']is None or slot['closed']
  for group in (retirement['slots'],retirement['physical_slots']) if group is not None for slot in group)
 _f._scan_raise_errors(errors)
 _f._preflight_require_v1(retirement['complete'],
  'ORDINARY_INITIAL_EVERY_ORIGINAL_LOCAL_LOAN_ONE_CLOSED')
 return retirement


def _ordinary_ci_initial_direct_request_v1(reliability, source_generation):
 """Prospective direct QTT effects, separately from the trusted environment."""
 # This is the selected CPython 3.14.6 GIL/LP64 Source branch, not an ABI receipt.
 # The actual ABI observer must independently join it before later DATA use.
 layout={'sizes':(('pointer',8),('gc',16),('bytes_prefix',33),
  ('bytearray_prefix',56),('unicode_prefix',64),('tuple_prefix',48),
  ('list_prefix',56),('dict_prefix',64),('dict_keys_prefix',32),
  ('dict_unicode_entry',16),('dict_general_entry',24),('int_prefix',24),
  ('int_digit_bits',30),('int_digit_bytes',4),('control_integer',44))}
 data=reliability.__dict__
 expected=('_ordinary_data_bytes_request_v1','_ordinary_data_unicode_request_v1',
  '_ordinary_data_tuple_request_v1','_ordinary_data_list_requests_v1',
  '_ordinary_data_dict_requests_v1','_ordinary_initialized_storage_data_request_v1')
 from types import FunctionType
 if any(type(data.get(name))is not FunctionType or data[name].__globals__ is not data
  for name in expected):raise ValueError('ORDINARY_INITIAL_FIXED_DATA_OWNERS')
 B=lambda n:data[expected[0]](layout,n)
 U=lambda n:data[expected[1]](layout,n)
 T=lambda n:data[expected[2]](layout,n)
 L=lambda n,s:data[expected[3]](layout,n,s)
 D=lambda n,k:data[expected[4]](layout,n,k)
 from pathlib import PosixPath
 import os
 if type(source_generation)is not dict:
  raise ValueError('ORDINARY_INITIAL_ORIGINAL_LEXICAL_PATH_OPERANDS')
 original=source_generation.get('original')
 if type(original)is not tuple or len(original)!=17 or original[0]is not source_generation or type(original[14])is not tuple or len(original[14])!=6 or type(original[13])is not PosixPath or any(type(path)is not PosixPath for path in original[14]) or data.get('os')is not os:
  raise ValueError('ORDINARY_INITIAL_ORIGINAL_LEXICAL_PATH_OPERANDS')
 paths=(original[13],*original[14])
 temporary=os.environ.get('RUNNER_TEMP')
 if type(temporary)is not str or not temporary or len(temporary.encode('utf-8'))>4096 or any(len(str(path).encode('utf-8'))>4096 for path in paths):
  raise ValueError('ORDINARY_INITIAL_LEXICAL_PATH_UTF8_DOMAIN')
 # These are original lexical operands, not observed physical metadata.
 # Selected system/cgroup paths are ASCII; user root paths derive from the
 # same original Source paths and admitted complete inherited environment.
 path_values=tuple(map(str,paths))
 lexical_path=max(len(temporary),*map(len,path_values))+192
 issue=source_generation['original'][1]['initial_request_issuer']
 if (type(issue)is not dict or issue['source_generation']is not source_generation
  or issue['complete']is not False or issue.get('path_stock_original')is not None):
  raise ValueError('ORDINARY_INITIAL_ONE_ORIGINAL_PATH_STOCK_ISSUANCE')
 issue['path_stock_original']=(issue,source_generation,original,paths,path_values,temporary,
  lexical_path,_ordinary_ci_initial_direct_request_v1,_ordinary_ci_initial_direct_request_v1.__code__)
 work_loops=8*(8192+1025);settlement_loops=1025
 # ONE generic variable acquisition contribution includes every supervisor,
 # direct kernel, Input4 pair and getter attempt. No per-file renewal.
 origin_paths=35*65
 origin_fixed=5*origin_paths+2*28+45+26
 input4_paths=17*65
 input4_fixed=5*input4_paths+85*(3+64)+136+153+16+20+4352+26+12+1
 physical_paths=38*65
 physical_fixed=9*(6*65-1)+29*(7*65+4)+9*(65+2)+(65+2)+132+8*(65+2)+3+1+6+8
 # Fixed original maps metadata/component work and bounded original parser
 # rows stay separate from variable raw-read progress in the SAME counter.
 getter_fixed=20+1048576//17
 supervisor_fixed=8*17
 keeper_fixed=77+13*91
 work_fixed=origin_fixed+input4_fixed+physical_fixed+getter_fixed+supervisor_fixed+keeper_fixed+7
 close_fixed=origin_paths+input4_paths+physical_paths+3*(15+17+38)+4
 limits=dict(work_calls=work_loops+work_fixed,work_bytes=24510502,
  settlement_calls=7*settlement_loops+8*13+4*2*1025+close_fixed,
  settlement_bytes=32<<20,work_loops=work_loops,settlement_loops=settlement_loops)
 calls=limits['work_calls']+limits['settlement_calls']
 # Source slots are actual dictionaries/journals, not arbitrary fixed parts.
 records=D(1,14)+T(10)+T(7)+T(12)+D(2,12)+T(4)+T(2)+T(6)+6*T(2)
 records+=D(1,8)+T(8)+T(5)+T(2)+D(1,21)+T(9)+T(14)+T(11)
 records+=D(1,5)+8*(D(1,9)+D(3,36)+D(5,40)+D(2,32)+D(1,3)
  +D(2,14)+D(1,40)+L(8,32)+T(7)+3*T(4)+5*T(6))
 paths=origin_paths+input4_paths+physical_paths
 records+=D(paths,15*paths)+D(29+28,9*(29+28))+D(8,14*8)+D(16,11*16)
 records+=D(1,38)+T(16)+T(15)+T(12)+D(1,18)+D(1,30)+T(18)+T(17)
 records+=L(9,paths+57+16)+L(paths+100,2*(paths+100))
 path_copies=paths*(max(3*U(lexical_path),3*(64+4096+1))+3*T(65)+33*44+T(4))
 # Every retained full-read prefix shares the original aggregate returned
 # pool. Actual bytearray growth, final bytes and one active last chunk are
 # funded; FILE128 is a read-domain guard, never a demand or success receipt.
 raw=4*limits['work_bytes']+73*(56+B(65536)+33)
 # Original Input4 full.acquire() overwrites ONE attempt per slot and
 # directly debits READ/RETURNED; it appends no per-read call() dictionary.
 # Fixed nonread call() records are distinct from the shared pointer log.
 journal_rows=input4_fixed+2
 records+=D(journal_rows,9*journal_rows)+journal_rows*(T(4)+D(1,2)+44)
 metadata_rows=3*input4_paths+2*85+28
 records+=metadata_rows*(T(32)+32*44+3*24)+L(4,4*journal_rows)
 # Origin effect() generates bounded fresh labels only at fixed call sites;
 # read/open/close labels and the other Source operation labels are constants.
 records+=45*U(64)+16*D(1,13)+16*T(2)
 actor_tokens=65536//2+1
 parsing=4*(B(65536)+L(1,actor_tokens)+actor_tokens*B(0)+65536+T(3)+3*44)
 parsing+=8*(B(4096)+L(1,4097)+4097*B(0)+4096+3*B(4096)+3*U(4096)+T(3)+D(1,7))
 # The first failed Popen may retain its bounded errorpipe and four active
 # buffered objects. Successful closes release buffers; wrappers stay held.
 errorpipe=56+2*(100000+100000//8+7)+B(50000)+B(100000)+U(100000)+L(1,3)+3*B(100000)
 # The same sequential supervisor closes each successful pipe/evidence
 # stream before the next call. Its closed wrapper remains; backing buffers
 # are one active four-stream set. Only the first failing Popen can retain
 # its errorpipe; sticky original errors veto every subsequent dispatch.
 io=4*(1<<20)+8*4*(152+16+56+16+19*8)+errorpipe
 chunks=2*(B(65536)+B(4096))+16*B(65536)+18*44
 # Actual receipt publication projects a fixed bounded shape; ASCII escaping
 # can expand each input character sixfold. Source strings are prospectively
 # derived from the selected direct closure, not a post-optimized Code quota.
 bodies,slots,string_chars,initializer_units=(0x000018dd,0x001da1c0,0x0003ee1f,0x00001700)
 success_chars=4*(4096+32)+8*4096
 failure_chars=success_chars+string_chars+100000
 # First-error dispatch stops the remaining original command list. Seven
 # successful fixed receipts may coexist with one failure diagnostic; no
 # successful receipt acquires another failing-Popen errorpipe payload.
 text=7*(3*U(success_chars)+3*U(6*success_chars)+B(6*success_chars)+3*D(3,45)+L(3,200))
 text+=3*U(failure_chars)+3*U(6*failure_chars)+B(6*failure_chars)+3*D(3,45)+L(3,200)
 frames=bodies*(72+80+16)+8*slots
 functions=bodies*(152+16)+bodies*48+8*slots+slots*(24+16)
 # One failed dispatch halts later commands. The thirteen distinct settling
 # callees each retain at most their same closed direct Source call chain.
 failures=14*(frames+bodies*(40+16)+112+48+3*8)
 maps_request=data[expected[5]](layout)
 components=(('original_initial_request_prefix_issuer_and_supervisor_records',records),
  ('original_initial_complete_path_versions_and_strings',path_copies),
  ('original_initial_physical_and_independent_source_pair_raw_prefixes',raw),
  ('original_initial_closed_manager_and_actor_parser_data',parsing),
  ('original_initial_active_io_retained_wrappers_and_errorpipe',io+chunks),
  ('original_initial_receipt_projection_and_publication',text),
  ('original_initial_source_frames_closures_and_first_failure_cleanup',frames+functions+failures),
  ('original_initial_complete_shared_operation_pointer_log',L(1,calls+1)),
  ('original_initial_retained_preloader_code_identity_walk',
   L(1,initializer_units)+64+2*16*(8+6*initializer_units)+initializer_units*36),
  *maps_request['components'])
 if (any(type(label)is not str or not label or type(value)is not int or value<0
  for label,value in components) or len({label for label,_ in components})!=len(components)):
  raise ValueError('ORDINARY_INITIAL_COMPLETE_SOURCE_COMPONENT_SHAPE')
 return components,limits


def _ordinary_ci_initial_path_stock_v1(native_input, value):
 """Admit the original priced lexical path before any component allocation."""
 from pathlib import PosixPath
 from types import FunctionType
 import os
 if type(native_input)is not dict or type(value)not in(str,PosixPath):
  raise ValueError('ORDINARY_INITIAL_PATH_STOCK_EXACT_INTERNAL_OPERANDS')
 issue=native_input.get('initial_request_issuer')
 if type(issue)is not dict or issue.get('native_input')is not native_input:
  raise ValueError('ORDINARY_INITIAL_PATH_STOCK_ORIGINAL_ISSUER')
 old=issue.get('path_stock_original');source=issue.get('source_generation')
 original=source.get('original')if type(source)is dict else None
 result=issue.get('result_original');allocation=issue.get('allocation')
 if (type(source)is not dict or type(original)is not tuple or len(original)!=17
  or original[0]is not source or original[1]is not native_input
  or type(original[14])is not tuple or len(original[14])!=6
  or type(result)is not tuple or len(result)!=7
  or type(allocation)is not tuple or len(allocation)!=4
  or allocation[0]is not native_input or allocation[1]is not issue.get('result')
  or type(old)is not tuple or len(old)!=9
  or old[0]is not issue or old[1]is not source or old[2]is not source.get('original')
  or type(old[3])is not tuple or len(old[3])!=7
  or type(old[4])is not tuple or len(old[4])!=7
  or any(type(v)is not PosixPath for v in old[3])
  or any(type(v)is not str for v in old[4])
  or type(old[5])is not str or old[5]!=os.environ.get('RUNNER_TEMP')
  or type(old[6])is not int or old[6]!=max(len(old[5]),*map(len,old[4]))+192
  or old[7]is not _ordinary_ci_initial_direct_request_v1
  or type(old[7])is not FunctionType or old[8]is not old[7].__code__
  or old[7].__globals__ is not globals()
  or original[13]is not old[3][0]
  or any(a is not b for a,b in zip(original[14],old[3][1:]))
  or tuple(map(str,old[3]))!=old[4]
  or issue.get('complete')is not True
  or issue['result']is not native_input.get('early_profile')
  or issue['allocation']is not native_input.get('early_allocation_original')
  or issue['result_original'][0]is not issue
  or issue['result_original'][4]is not issue['allocation']):
  raise ValueError('ORDINARY_INITIAL_PATH_STOCK_UNCHANGED_SOURCE_AND_ISSUANCE')
 text=value if type(value)is str else str(value)
 if len(text)>old[6] or len(text.encode('utf-8'))>4096:
  raise ValueError('ORDINARY_INITIAL_PATH_EXCEEDS_ORIGINAL_PRICED_STOCK')
 return value


def _facet_fn_initial_keeper_observation_loans_v1(native_input, record, holder, root):
 """Adopt only the original keeper's three gated PROVISION readonly observations."""
 import tools.validation_reliability as _f
 prefix=_f._ordinary_initial_prefix_v1(native_input);owner=prefix['owner'];errors=prefix['errors']
 caller=_f.sys._getframe(1)
 try:
  _f._preflight_require_v1(record is native_input['origin_prebind'] and record['complete']is False
   and record['owner']is owner and record['errors']is errors and not errors
   and caller.f_code is record['producer_code'] and caller.f_globals is _f.__dict__
   and caller.f_locals.get('record')is record and caller.f_locals.get('native_input')is native_input
   and caller.f_locals.get('role')=='PROVISION' and caller.f_locals.get('holder')is holder
   and caller.f_locals.get('fd_root')is root and any(slot is root for slot in record['slots'])
   and root['owner']is owner and root['held']is True and not root['closed']
   and root['path']==_f.Path('/proc')/str(owner[0])/'fd'
   and record.get('keeper_observation_loans')is None,
   'ORDINARY_INITIAL_KEEPER_LOAN_FIXED_PROVISION_CALLER')
 finally:del caller
 fields=('native_input','prebind','prebind_original','source_anchor','holder','root','owner','errors',
  'producer','producer_code','module_namespace','initializer_code','slots','observations','roles')
 value=dict(native_input=native_input,prebind=record,prebind_original=record['original'],
  source_anchor=native_input['preloader_source_anchor'],holder=holder,root=root,owner=owner,errors=errors,
  producer=_facet_fn_initial_keeper_observation_loans_v1,
  producer_code=_facet_fn_initial_keeper_observation_loans_v1.__code__,module_namespace=globals(),
  initializer_code=globals()['_ORDINARY_INITIALIZED_MODULE_CODE_V1'],slots=[],observations=[],roles={},
  iterator=None,iterator_close_attempted=False,iterator_closed=False,iterator_descriptor=None,
  active_operation=None,loop_attempts=0,seen_fds=set(),complete=False,product_association=None)
 record['keeper_observation_loans']=value
 value['original']=(value,)+tuple(value[name]for name in fields)
 def call(name,function,*args,settling=False,**kwargs):
  name='ORIGIN_PREBIND_'+name;value['active_operation']=record['active_operation']=name
  row=dict(operation=name,function=function,args=args,kwargs=kwargs,attempted=False,
   returned=None,error=None,settling=settling)
  value['observations'].append(row)
  try:
   _f._ordinary_initial_native_debit_v1(native_input,name,settling=settling)
   row['attempted']=True;row['returned']=function(*args,**kwargs);return row['returned']
  except BaseException as error:row['error']=error;raise
  finally:value['active_operation']=record['active_operation']=None
 try:
  module=call('OWNER',__import__,'fcntl')
  _f._preflight_require_v1(_f.sys.modules.get('fcntl')is module
   and type(module.ioctl)is type(_f.os.fstat) and type(module.fcntl)is type(_f.os.fstat),
   'ORDINARY_INITIAL_KEEPER_LOAN_TRUSTED_READONLY_FCNTL')
  actual_root=call('HANDLE_METADATA',_f.os.fstat,root['returned_fd'])
  _f._preflight_require_v1(_f._preflight_stamp_v1(actual_root)==root['handle_version']
   and not call('INHERITANCE',_f.os.get_inheritable,root['returned_fd']),
   'ORDINARY_INITIAL_KEEPER_LOAN_SAME_FD_CENSUS_ROOT')
  holder_proc=next(slot for slot in record['slots']if slot.get('path')==_f.Path('/proc')/str(holder[0])
   and not slot['closed']and slot['held'])
  _f._preflight_require_v1(holder_proc['owner']is owner and holder_proc['uid']==holder_proc['gid']==0,
   'ORDINARY_INITIAL_KEEPER_LOAN_ORIGINAL_PRIVILEGED_HOLDER')
  named=call('PATH_METADATA',_f.os.stat,'maps',dir_fd=holder_proc['returned_fd'],follow_symlinks=False)
  _f._preflight_require_v1(_f.stat.S_ISREG(named.st_mode)and named.st_uid==named.st_gid==0
   and named.st_nlink==1 and named.st_size==0,
   'ORDINARY_INITIAL_KEEPER_LOAN_ACTUAL_HOLDER_PROC_MAPS')
  iterator=call('OWNER',_f.os.scandir,root['returned_fd']);value['iterator']=iterator
  failure=[]
  try:
   while True:
    allocation=native_input['early_allocation_original'];value['loop_attempts']+=1
    allocation[3]['work_loops']+=1
    _f._preflight_require_v1(value['loop_attempts']<=65
     and allocation[3]['work_loops']<=allocation[2]['work_loops'],
     'ORDINARY_INITIAL_KEEPER_LOAN_BOUNDED_SHARED_FD_CENSUS')
    try:item=call('OWNER',next,iterator)
    except StopIteration:break
    _f._preflight_require_v1(type(item.name)is str and _f.re.fullmatch(r'0|[1-9][0-9]{0,9}',item.name)
     and int(item.name)<(1<<31),'ORDINARY_INITIAL_KEEPER_LOAN_CANONICAL_FD_NAME')
    descriptor=int(item.name)
    _f._preflight_require_v1(descriptor not in value['seen_fds'],
     'ORDINARY_INITIAL_KEEPER_LOAN_NO_REPEATED_DESCRIPTOR_NAME')
    value['seen_fds'].add(descriptor)
    if descriptor<=2:continue
    existing=tuple(slot for slot in record['slots']if slot.get('returned_fd')==descriptor and not slot['closed'])
    if existing:
     _f._preflight_require_v1(len(existing)==1 and existing[0]['owner']is owner
      and not call('INHERITANCE',_f.os.get_inheritable,descriptor),
      'ORDINARY_INITIAL_KEEPER_LOAN_ALREADY_OWNED_NONINHERITED_FD')
     continue
    info=call('HANDLE_METADATA',_f.os.fstat,descriptor)
    flags=call('HANDLE_METADATA',module.fcntl,descriptor,module.F_GETFL)
    inherited=call('INHERITANCE',_f.os.get_inheritable,descriptor)
    if _f.stat.S_ISDIR(info.st_mode)and _f._same_observed_file(info,actual_root):
     _f._preflight_require_v1(value['iterator_descriptor']is None and not inherited
      and _f.stat.S_ISDIR(info.st_mode)and flags&_f.os.O_ACCMODE==_f.os.O_RDONLY,
      'ORDINARY_INITIAL_KEEPER_LOAN_SOLE_ACTUAL_CENSUS_ITERATOR_FD')
     value['iterator_descriptor']=descriptor;continue
    slot=dict(owner=owner,returned_fd=descriptor,open_attempted=False,adoption_attempted=True,
     close_admission_attempted=False,close_attempted=False,closed=False,held=True,errors=[],
     handle_version=_f._preflight_stamp_v1(info),role=None,flags=flags,inherited_before=inherited,
     source_loan=value,noninherit_attempted=False,noninherit_returned=False)
    _f._preflight_require_v1(len(value['slots'])<3 and inherited
     and _f.stat.S_ISREG(info.st_mode)and info.st_nlink==1
     and info.st_uid==info.st_gid==0 and flags&_f.os.O_ACCMODE==_f.os.O_RDONLY
     and not flags&getattr(_f.os,'O_PATH',0),
     'ORDINARY_INITIAL_KEEPER_LOAN_EXACT_THREE_INHERITED_READONLY_ROLES')
    if _f._same_observed_file(info,named):
     _f._preflight_require_v1(_f._preflight_stamp_v1(info)==_f._preflight_stamp_v1(named)
      and call('HANDLE_METADATA',_f.os.lseek,descriptor,0,_f.os.SEEK_CUR)==0,
      'ORDINARY_INITIAL_KEEPER_LOAN_AUTHORIZED_ORIGINAL_MAPS_FD')
     role='KEEPER_MAPS';slot['path']=holder_proc['path']/'maps';slot['path_version']=_f._preflight_stamp_v1(named)
    else:
     kind=call('NAMESPACE',module.ioctl,descriptor,0xb703,0)
     _f._preflight_require_v1(type(kind)is int and kind in(0x02000000,0x00020000)
      and _f.stat.S_IMODE(info.st_mode)==0o444 and info.st_size==0,
      'ORDINARY_INITIAL_KEEPER_LOAN_ACTUAL_NSFS_ROLE')
     role='CGROUP_NAMESPACE'if kind==0x02000000 else'MOUNT_NAMESPACE';slot['namespace_type']=kind
     own=call('NAMESPACE',_f.os.stat,'/proc/'+str(owner[0])+'/ns/'+('cgroup'if kind==0x02000000 else'mnt'))
     _f._preflight_require_v1((info.st_dev,info.st_ino)==(own.st_dev,own.st_ino),
      'ORDINARY_INITIAL_KEEPER_LOAN_ORIGINAL_FORK_SAME_ACTUAL_NAMESPACE')
    _f._preflight_require_v1(role not in value['roles'],'ORDINARY_INITIAL_KEEPER_LOAN_NO_DUPLICATE_ROLE')
    slot['role']=role;value['roles'][role]=slot
    value['slots'].append(slot);record['slots'].append(slot)
    slot['noninherit_attempted']=True
    call('INHERITANCE',_f.os.set_inheritable,descriptor,False);slot['noninherit_returned']=True
    _f._preflight_require_v1(not call('INHERITANCE',_f.os.get_inheritable,descriptor),
     'ORDINARY_INITIAL_KEEPER_LOAN_NO_FUTURE_DESCENDANT_INHERITANCE')
    slot['original']=(slot,value,record,holder,descriptor,slot['handle_version'],flags,role,owner,errors)
    after=call('HANDLE_METADATA',_f.os.fstat,descriptor)
    _f._preflight_require_v1(_f._preflight_stamp_v1(after)==slot['handle_version']
     and not call('INHERITANCE',_f.os.get_inheritable,descriptor),
     'ORDINARY_INITIAL_KEEPER_LOAN_SAME_ADOPTED_HANDLE_GENERATION')
  except BaseException as error:failure.append(error)
  finally:
   value['iterator_close_attempted']=True
   try:call('ONE_CLOSE',iterator.close,settling=True);value['iterator_closed']=True
   except BaseException as error:failure.append(error)
  _f._scan_raise_errors(failure)
  _f._preflight_require_v1(len(value['slots'])==3 and set(value['roles'])=={
   'CGROUP_NAMESPACE','MOUNT_NAMESPACE','KEEPER_MAPS'}and value['iterator_descriptor']is not None
   and value['iterator_closed'],'ORDINARY_INITIAL_KEEPER_LOAN_EXACT_COMPLETED_ROLE_CENSUS')
  _f._preflight_require_v1(_f._preflight_stamp_v1(call('PATH_REJOIN',_f.os.stat,'maps',
   dir_fd=holder_proc['returned_fd'],follow_symlinks=False))==value['roles']['KEEPER_MAPS']['path_version'],
   'ORDINARY_INITIAL_KEEPER_LOAN_SAME_LIVING_MAPS_PROC_GENERATION')
  value['complete']=True;return value
 except BaseException as error:
  if not any(error is old for old in errors):errors.append(error)
  raise


def _facet_fn_initial_startup_prebind_v1(native_input):
 """Rejoin the same completed C keeper before the original cold constructor."""
 import tools.validation_reliability as _f
 require=_f._preflight_require_v1
 _f._ordinary_initial_preloader_return_check_v1(native_input)
 prefix=_f._ordinary_initial_prefix_v1(native_input)
 generation=native_input['source_generation'];startup=native_input['startup_source']
 original=generation['original'];errors=native_input['errors'];owner=native_input['owner']
 origin=native_input['origin_prebind'];origin_original=origin['result_original']
 require(owner==(_f.os.getpid(),_f.threading.get_ident())and not errors
  and native_input['native_instance']is None and not native_input['native_init_attempted']
  and origin['complete']is True and origin_original is native_input['origin_prebind_result_original']
  and origin_original[0]is origin and origin_original[1]is origin['original']
  and origin_original[10]is native_input['original_origin_request']
  and origin_original[11]is errors and origin['owner']is owner
  and origin['operations']is prefix['operations']and 'retirement'not in origin
  and startup['startup_binding']is None and startup['roles']is None
  and 'pre_cold_attempt'not in startup,'INITIAL_STARTUP_ONE_ORIGINAL_PRE_COLD_REJOIN')
 caller=_f.sys._getframe(2)
 try:
  require(caller.f_globals is _f.__dict__
   and caller.f_code is _f._ordinary_initial_native_object_v1.__code__
   and caller.f_locals.get('native_input')is native_input
   and caller.f_locals.get('source_return')is native_input['preloader_source_return'],
   'INITIAL_STARTUP_ORIGINAL_PRE_COLD_CALLER')
 finally:del caller
 operands=origin['operands'];original_cutoffs=origin['cutoffs']
 a=dict(native_input=native_input,generation=generation,startup=startup,
  source_original=original,origin=origin,origin_original=origin_original,
  owner=owner,cutoffs=original_cutoffs,errors=errors,slots=origin['slots'],reads=origin['reads'],
  operations=[],returned=[],iterators=[],pending_acl=[],source_pairs=[],complete=False,
  producer=_facet_fn_initial_startup_prebind_v1,producer_code=_facet_fn_initial_startup_prebind_v1.__code__)
 startup['pre_cold_attempt']=a
 a['original']=(a,native_input,generation,startup,original,origin,origin_original,owner,
  original_cutoffs,errors,a['slots'],a['reads'],a['operations'],a['pending_acl'],
  a['source_pairs'],a['producer'],a['producer_code'])
 binding=a
 physical=dict(slots=a['slots'],reads=a['reads'])
 def call(label,function,*args,settling=False,**kwargs):
  row=dict(label=label,function=function,args=args,kwargs=kwargs,
   admission_attempted=True,attempted=False,result=None,error=None,settling=settling)
  a['operations'].append(row)
  try:
   _f._ordinary_initial_native_debit_v1(native_input,label,settling=settling)
   row['attempted']=True;row['result']=function(*args,**kwargs);return row['result']
  except BaseException as error:row['error']=error;raise
 def v9(info):
  return(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid,
   info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
 def v11(info):
  return[info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,
   info.st_ctime_ns,info.st_nlink,info.st_uid,info.st_gid,
   getattr(info,'st_file_attributes',0),getattr(info,'st_reparse_tag',0)]
 def path(value):
  _ordinary_ci_initial_path_stock_v1(native_input,value)
  require(type(value)is str and value.startswith('/')and value!='/'and '\\'not in value
   and not any(c in value for c in ('\0','\n','\r'))
   and len(value.encode('utf-8'))<=4096 and len(value.split('/'))<=65
   and all(part and part not in ('.','..')and len(part.encode('utf-8'))<=255
    for part in value.split('/')[1:]),'INITIAL_STARTUP_FIXED_ABSOLUTE_COMPONENTS')
  return _f.Path(value)
 def close(slot):
  require(not slot['close_admission_attempted']and not slot['close_attempted']
   and not slot['closed']and type(slot['returned_fd'])is int,
   'INITIAL_STARTUP_ORIGINAL_ONE_CLOSE')
  slot['close_admission_attempted']=True
  _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True)
  slot['close_attempted']=True
  try:_f.os.close(slot['returned_fd']);slot['closed']=True
  except BaseException as error:slot['errors'].append(error);raise
 def opened(value,directory=False):
  selected=path(str(value));previous=None
  for index,component in enumerate(('/',*selected.parts[1:])):
   final=index==len(selected.parts)-1
   slot=dict(owner=owner,path=_f.Path('/')if index==0 else previous['path']/component,
    component=component,parent=previous,returned_fd=None,open_attempted=False,
    close_admission_attempted=False,close_attempted=False,closed=False,held=False,errors=[],complete=False)
   physical['slots'].append(slot)
   try:
    args={}if previous is None else dict(dir_fd=previous['returned_fd'])
    before=call('INITIAL_STARTUP_PATH_METADATA',_f.os.stat,component,follow_symlinks=False,**args)
    slot['path_version']=_f._preflight_stamp_v1(before)
    slot['uid'],slot['gid']=before.st_uid,before.st_gid
    require(not _f._stat_is_reparse_point(before)and not _f.stat.S_ISLNK(before.st_mode)
     and (_f.stat.S_ISDIR(before.st_mode)if not final or directory else
      _f.stat.S_ISREG(before.st_mode)and before.st_nlink==1),'INITIAL_STARTUP_NOFOLLOW_KIND')
    flags=_f.os.O_RDONLY|_f.os.O_NOFOLLOW|_f.os.O_CLOEXEC|_f.os.O_NONBLOCK
    if not final or directory:flags|=_f.os.O_DIRECTORY
    _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_COMPONENT_OPEN')
    slot['open_attempted']=True;slot['returned_fd']=_f.os.open(component,flags,**args)
    held=call('INITIAL_STARTUP_HANDLE_METADATA',_f.os.fstat,slot['returned_fd'])
    after=call('INITIAL_STARTUP_PATH_REJOIN',_f.os.stat,component,follow_symlinks=False,**args)
    require(v11(before)==v11(held)==v11(after)
     and not call('INITIAL_STARTUP_INHERITANCE',_f.os.get_inheritable,slot['returned_fd']),
     'INITIAL_STARTUP_COMPLETE_PATH_HANDLE_GENERATION')
    slot['handle_version']=_f._preflight_stamp_v1(held)
    slot['version']=v11(held);slot['version9']=v9(held)
    if previous is not None:close(previous)
    previous=slot
   except BaseException as error:slot['errors'].append(error);raise
  slot['held']=True;return slot
 def rejoin(slot,directory=False,protected=False):
  require(slot['owner']is owner and not slot['close_admission_attempted']
   and not slot['close_attempted']and not slot['closed'],
   'INITIAL_STARTUP_RETAINED_ORIGINAL_DESCRIPTOR')
  held=call('INITIAL_STARTUP_HELD_REJOIN',_f.os.fstat,slot['returned_fd'])
  named=call('INITIAL_STARTUP_NAMED_REJOIN',_f.os.lstat,slot['path'])
  require(v11(held)==v11(named)==slot['version']and v9(held)==slot['version9']
   and not _f._stat_is_reparse_point(named)and not _f.stat.S_ISLNK(named.st_mode)
   and (_f.stat.S_ISDIR(held.st_mode)if directory else
    _f.stat.S_ISREG(held.st_mode)and held.st_nlink==1)
   and not call('INITIAL_STARTUP_HELD_INHERITANCE',_f.os.get_inheritable,slot['returned_fd']),
   'INITIAL_STARTUP_UNCHANGED_COMPLETE_CURRENT_GENERATION')
  parent=slot['parent']
  while parent is not None:
   info=call('INITIAL_STARTUP_ANCESTOR_REJOIN',_f.os.lstat,parent['path'])
   require(_f.stat.S_ISDIR(info.st_mode)and not _f._stat_is_reparse_point(info)
    and (info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
     ==(*parent['path_version'][:3],parent['uid'],parent['gid']),
     'INITIAL_STARTUP_UNCHANGED_NOFOLLOW_ANCESTRY')
   parent=parent['parent']
  if protected:
   require(call('INITIAL_STARTUP_PROTECTED_FLAGS',flags,slot['returned_fd'])==slot['flags'],
    'INITIAL_STARTUP_SAME_PROTECTED_FLAGS')
  return held
 def delivered(raw,request,label):
  note=dict(raw=raw,request_bytes=request,label=label,debited=False)
  a['returned'].append(note)
  _f._ordinary_initial_native_debit_v1(native_input,label,raw=raw,request_bytes=request)
  note['debited']=True
 def full(slot,extent):
  require(type(extent)is int and 0<=extent<=134217728,'INITIAL_STARTUP_ORIGINAL_FILE128_DOMAIN')
  attempt=dict(complete=True)
  slot.update(prefix=bytearray(),last_returned=None,returned_bytes=0,raw=None,complete=False,
   read_attempt=attempt,read_attempts=0,read_admission_attempts=0,read_admitted_calls=0,
   read_native_attempts=0,read_bytes_debited=0,successful_reads=0,successful_bytes=0,eof_observed=False)
  physical['reads'].append(slot)
  call('INITIAL_STARTUP_REWIND',_f.os.lseek,slot['returned_fd'],0,_f.os.SEEK_SET)
  def acquire(desired,eof):
   require(attempt['complete']is True,'INITIAL_STARTUP_PREVIOUS_READ_COMMITTED')
   # ONE slot-local attempt survives until its actual delivery commits.
   # Successful advances overwrite it; the original shared debit ledger persists.
   attempt.clear();attempt.update(label='INITIAL_STARTUP_EOF'if eof else'INITIAL_STARTUP_READ',
    desired=desired,request=None,quantum_attempted=True,admission_attempted=False,
    attempted=False,result=None,byte_admission_attempted=False,debited=False,
    eof=eof,complete=False,error=None)
   slot['read_attempts']+=1
   try:
    request=_f._ordinary_initial_native_quantum_v1(native_input,desired)
    attempt['request']=request;attempt['admission_attempted']=True
    slot['read_admission_attempts']+=1
    _f._ordinary_initial_native_debit_v1(native_input,attempt['label'])
    slot['read_admitted_calls']+=1;attempt['attempted']=True
    slot['read_native_attempts']+=1
    block=_f.os.read(slot['returned_fd'],request)
    attempt['result']=slot['last_returned']=block
    slot['returned_bytes']+=len(block);attempt['byte_admission_attempted']=True
    _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_RETURNED_BYTES',
     raw=block,request_bytes=request)
    attempt['debited']=True;slot['read_bytes_debited']+=len(block)
    slot['prefix'].extend(block)
    require((not block and slot['returned_bytes']==extent)if eof else
     (block and slot['returned_bytes']<=extent),
     'INITIAL_STARTUP_EXACT_EOF'if eof else'INITIAL_STARTUP_COMPLETE_PROGRESS')
    slot['successful_reads']+=1;slot['successful_bytes']+=len(block)
    if eof:slot['eof_observed']=True
    attempt['complete']=True
   except BaseException as error:
    attempt['error']=error
    if all(error is not old for old in slot['errors']):slot['errors'].append(error)
    if all(error is not old for old in errors):errors.append(error)
    raise
  while len(slot['prefix'])<extent:acquire(min(65536,extent-len(slot['prefix'])),False)
  acquire(1,True)
  rejoin(slot,protected=True);slot['raw']=bytes(slot['prefix']);slot['complete']=True
  return slot['raw']
 def flags(fd):
  _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_FIXED_FCNTL_IMPORT')
  import fcntl
  module=_f.sys.modules.get('fcntl')
  require(type(module)is type(_f.sys)and module.__dict__.get('ioctl')is fcntl.ioctl
   and type(fcntl.ioctl)is type(len),'INITIAL_STARTUP_FIXED_READONLY_FLAGS_PRIMITIVE')
  buffer=bytearray(4)
  result=call('INITIAL_STARTUP_READONLY_FLAGS',fcntl.ioctl,fd,0x80086601,buffer,True)
  require(type(result)is int and result==0 and len(buffer)==4,
   'INITIAL_STARTUP_ACTUAL_READONLY_FLAGS_RETURN')
  raw=bytes(buffer);delivered(raw,4,'INITIAL_STARTUP_FLAGS_RETURNED_BYTES')
  return int.from_bytes(raw,_f.sys.byteorder)
 def acl(slot):
  require('acl_pending_original'not in slot,'INITIAL_STARTUP_ONE_PENDING_ORIGINAL_ACL')
  note=dict(slot=slot,path=str(slot['path']),version=slot['version'],version9=slot['version9'],
   flags=slot['flags'],owner=owner,errors=errors,complete=False,result=None)
  note['original']=(note,a,slot,note['path'],note['version'],note['version9'],
   note['flags'],owner,errors)
  slot['acl_pending_original']=note;a['pending_acl'].append(note)
 def physical_live():
  require(origin['complete']is True and origin['result_original']is origin_original
   and native_input['origin_prebind_result_original']is origin_original
   and origin['owner']is owner and origin['errors']is errors
   and origin['cutoffs']is original_cutoffs and 'retirement'not in origin,
   'INITIAL_STARTUP_SAME_EARLIER_ORIGINAL_KEEPER')
  select=_f.sys.modules.get('select')
  require(type(select)is type(_f.sys),'INITIAL_STARTUP_SAME_ADMITTED_SELECT_MODULE')
  poll=call('INITIAL_STARTUP_KEEPER_POLL',select.poll)
  for slot in origin['living_pidfds']:
   require(not slot['closed']and slot['held']and not slot['close_attempted'],
    'INITIAL_STARTUP_HELD_ORIGINAL_KEEPER_PIDFD')
   metadata=call('INITIAL_STARTUP_KEEPER_PIDFD_METADATA',_f.os.fstat,slot['returned_fd'])
   require(_f._preflight_stamp_v1(metadata)==slot['handle_version']
    and not call('INITIAL_STARTUP_KEEPER_PIDFD_INHERITANCE',_f.os.get_inheritable,slot['returned_fd']),
    'INITIAL_STARTUP_SAME_ORIGINAL_LIFETIME_DESCRIPTOR')
   call('INITIAL_STARTUP_KEEPER_POLL_REGISTER',poll.register,slot['returned_fd'],select.POLLIN)
  require(not call('INITIAL_STARTUP_KEEPER_LIVING',poll.poll,0),
   'INITIAL_STARTUP_ORIGINAL_KEEPER_AND_ROLE_REMAIN_ALIVE')
  for slot in (origin['root'],*origin['held_cgroups'].values()):
   held=call('INITIAL_STARTUP_ORIGIN_HELD',_f.os.fstat,slot['returned_fd'])
   named=call('INITIAL_STARTUP_ORIGIN_NAMED',_f.os.lstat,slot['path'])
   require(_f._preflight_stamp_v1(held)==slot['handle_version']
    and _f._preflight_stamp_v1(named)==slot['path_version']and _f._same_observed_file(named,held),
    'INITIAL_STARTUP_UNCHANGED_EARLIER_ROOT_AND_CGROUPS')
 def readonly_raw(selected,baseline_path,extent=None):
  left=right=None;failures=[]
  note=dict(path=str(selected),baseline_path=str(baseline_path),source=None,baseline=None,
   raw=None,baseline_raw=None,complete=False,errors=failures)
  a['source_pairs'].append(note)
  try:
   left=opened(selected);note['source']=left;protected(left)
   right=opened(baseline_path);note['baseline']=right;protected(right,baseline=True)
   require(left['version9'][:2]!=right['version9'][:2]
    and left['version9'][6]==right['version9'][6]
    and (extent is None or left['version9'][6]<=extent),
    'INITIAL_STARTUP_INDEPENDENT_COMPLETE_FIXED_SOURCE_PAIR')
   note['raw']=full(left,left['version9'][6])
   note['baseline_raw']=full(right,right['version9'][6])
   require(note['raw']==note['baseline_raw'],'INITIAL_STARTUP_FIXED_ORIGINAL_SOURCE_BYTES')
   rejoin(left,protected=True);rejoin(right,protected=True);physical_live()
   note['original']=(note,a,left,right,note['raw'],note['baseline_raw'],errors)
  except BaseException as error:failures.append(error)
  finally:
   for slot in(right,left):
    if slot is not None and not slot['close_attempted']:
     try:close(slot)
     except BaseException as error:failures.append(error)
  _f._scan_raise_errors(failures)
  note['complete']=True;return note
 def bounded_proc(selected,limit):
  slot=opened(selected);failures=[];parts=bytearray()
  note=dict(slot=slot,prefix=parts,raw=None,complete=False,errors=failures)
  a['reads'].append(note)
  try:
   while True:
    request=_f._ordinary_initial_native_quantum_v1(native_input,min(65536,limit+1-len(parts)))
    require(request>0,'INITIAL_STARTUP_ORIGINAL_PROC_REQUEST')
    _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_PROC_READ')
    block=_f.os.read(slot['returned_fd'],request)
    delivered(block,request,'INITIAL_STARTUP_PROC_RETURNED_BYTES')
    parts.extend(block);require(len(parts)<=limit,'INITIAL_STARTUP_ORIGINAL_PROC_EXTENT')
    if not block:break
   rejoin(slot);note['raw']=bytes(parts);note['complete']=True;return note['raw']
  except BaseException as error:failures.append(error)
  finally:
   try:close(slot)
   except BaseException as error:failures.append(error)
   _f._scan_raise_errors(failures)
 def protected(slot,directory=False,baseline=False):
  info=rejoin(slot,directory=directory)
  mode=_f.stat.S_IMODE(info.st_mode)
  require(info.st_uid==info.st_gid==0 and mode==(0o555 if directory else 0o444)
   if directory or baseline else info.st_uid==info.st_gid==0 and mode in (0o444,0o555),
   'INITIAL_STARTUP_CURRENT_READONLY_OWNER_MODE')
  slot['flags']=call('INITIAL_STARTUP_FLAGS',flags,slot['returned_fd'])
  require(type(slot['flags'])is int and slot['flags']&16,'INITIAL_STARTUP_ACTUAL_IMMUTABLE')
  acl(slot);rejoin(slot,directory=directory,protected=True)
 try:
  physical_live()
  env=tuple((key,_f.os.environ.get(key))for key in
   ('GITHUB_WORKSPACE','RUNNER_TEMP','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'))
  require(all(type(value)is str and value for key,value in env),
   'INITIAL_STARTUP_ORIGINAL_FIXED_ENVIRONMENT')
  workspace,temp,run,attempt_name=(value for key,value in env)
  stem=operands['stem']
  attempt=dict(native_input=native_input,binding=a,physical=None,producer_original=a['original'],
   source_original=original,owner=owner,cutoffs=original_cutoffs,files={},directories={},
   aliases=[],file_order=[],directory_order=[],repeated_directories=[],pairs=[],module_observations=[],maps=[],
   symbols=[],absences=[],errors=errors,complete=False)
  attempt['original']=(attempt,native_input,a,origin,origin_original,original,owner,original_cutoffs,
   attempt['files'],attempt['directories'],attempt['aliases'],attempt['pairs'],errors)
  # These are exactly the original C source-selected roots, derived again
  # under the same fixed common stem. Current observations are never a claim
  # about the outside keeper's pre-protection transition or undo journal.
  require(env==tuple((key,_f.os.environ.get(key))for key in
   ('GITHUB_WORKSPACE','RUNNER_TEMP','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'))
   and workspace==env[0][1]and temp==env[1][1]and stem==operands['stem'],
   'INITIAL_STARTUP_SAME_ORIGINAL_INPUT4_ENVIRONMENT')
  install=path(_f.sys.prefix);control=path(temp)/(stem+'control')
  # Rejoin the actual sys.prefix spelling through the SAME finite alias
  # mechanics used by the outside original installation selector.
  for hop in range(64):
   changed=False;walked_prefix=''
   for index,component in enumerate(install.parts[1:]):
    walked_prefix+='/'+component
    before=call('INITIAL_STARTUP_ROOT_COMPONENT',_f.os.lstat,walked_prefix)
    require(not _f._stat_is_reparse_point(before),'INITIAL_STARTUP_ROOT_NO_REPARSE')
    if _f.stat.S_ISLNK(before.st_mode):
     target=call('INITIAL_STARTUP_ROOT_ALIAS',_f.os.readlink,walked_prefix)
     require(type(target)is str and target and len(target.encode('utf-8'))<=4096
      and not any(c in target for c in ('\0','\n','\r'))
      and v9(call('INITIAL_STARTUP_ROOT_ALIAS_REJOIN',_f.os.lstat,walked_prefix))==v9(before),
      'INITIAL_STARTUP_ROOT_ALIAS_ORIGINAL_GENERATION')
     attempt['aliases'].append((walked_prefix,target,v9(before)))
     replacement=target if target.startswith('/')else _f.os.path.dirname(walked_prefix)+'/'+target
     if index+1<len(install.parts)-1:replacement+='/'+ '/'.join(install.parts[index+2:])
     install=path(_f.os.path.normpath(replacement));changed=True;break
    require(_f.stat.S_ISDIR(before.st_mode),'INITIAL_STARTUP_ROOT_COMPONENT_DIRECTORY')
   if not changed:break
  else:raise ValueError('INITIAL_STARTUP_ORIGINAL_ROOT_ALIAS_DEPTH')
  control_slot=opened(control,True)
  ci=rejoin(control_slot,directory=True)
  require(ci.st_uid==ci.st_gid==0 and _f.stat.S_IMODE(ci.st_mode)==0o755,
   'INITIAL_STARTUP_OWNED_READONLY_LOAN_ROOT')
  attempt['control_root']=control_slot
  def installed(slot,directory=False):
   info=rejoin(slot,directory=directory)
   require(not info.st_mode&0o022,
    'INITIAL_STARTUP_ORIGINAL_INSTALLED_OWNER_MODE')
   slot['flags']=call('INITIAL_STARTUP_FLAGS',flags,slot['returned_fd'])
   require(type(slot['flags'])is int and slot['flags']&16,'INITIAL_STARTUP_ACTUAL_IMMUTABLE')
   acl(slot);rejoin(slot,directory=directory,protected=True)
  def dispose(slot,failures):
   if slot is not None and not slot['close_attempted']:
    try:close(slot)
    except BaseException as error:failures.append(error)
  def read_chunk(slot,request,label):
   quantum=_f._ordinary_initial_native_quantum_v1(native_input,request)
   require(quantum==request,'INITIAL_STARTUP_EXACT_REQUEST_PROSPECTIVE_ADMISSION')
   note=dict(request=request,label=label,result=None,error=None,debited=False)
   slot['startup_read_attempt']=note
   _f._ordinary_initial_native_debit_v1(native_input,label)
   try:
    raw=_f.os.read(slot['returned_fd'],request);note['result']=raw
    _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_RETURNED_BYTES',raw=raw,request_bytes=request)
    note['debited']=True;return raw
   except BaseException as error:note['error']=error;raise
  def compare_file(source_path,ordinal):
   selected=attempt['files'];key=str(source_path)
   require(key not in selected and len(selected)+len(attempt['directory_order'])<16380,
    'INITIAL_STARTUP_ORIGINAL_JOINT_C_FILE_DOMAIN')
   source=baseline=None;failures=[];record=dict(path=key,ordinal=ordinal,complete=False,
    metadata_complete=False,source=None,baseline=None,expected=None,comparison_bytes=0,errors=failures)
   selected[key]=record;attempt['file_order'].append(record)
   try:
    source=opened(source_path);record['source']=source;installed(source)
    baseline=opened(control/('file'+str(ordinal)));record['baseline']=baseline;protected(baseline,baseline=True)
    require(source['version9'][:2]!=baseline['version9'][:2]
     and source['version9'][6]==baseline['version9'][6]
     and 0<=source['version9'][6]<=134217728,'INITIAL_STARTUP_INDEPENDENT_ORIGINAL_FILE_EXTENT')
    record['version']=source['version'];record['logical_bytes']=source['version9'][6]
    record['observed_path']=key;record['aliases']=()
    record['original']=(record,attempt,binding,source,baseline,source['version9'],baseline['version9'])
    record['metadata_complete']=True
   except BaseException as error:failures.append(error)
   finally:dispose(baseline,failures);dispose(source,failures)
   _f._scan_raise_errors(failures)
   return record
  def directory(source_path,depth,recurse):
   key=str(source_path);require(depth<=64,'INITIAL_STARTUP_ORIGINAL_DIRECTORY_DEPTH')
   if key in attempt['directories']:
    prior=attempt['directories'][key]
    info=call('INITIAL_STARTUP_REPEATED_DIRECTORY',_f.os.lstat,source_path)
    attempt['repeated_directories'].append((key,prior,v9(info)))
    require(v9(info)==prior['source']['version9'],'INITIAL_STARTUP_REPEATED_ORIGINAL_DIRECTORY_GENERATION')
    physical_live();return
   source=baseline=None;iterator=None;failures=[];names=[];record=dict(path=key,
    complete=False,metadata_complete=False,duplicate=None,names=None,roster=None,members=[],source=None,baseline=None,errors=failures)
   attempt['directories'][key]=record;ordinal=len(attempt['directory_order'])
   try:
    source=opened(source_path,True);record['source']=source;installed(source,True)
    prior=tuple(row for row in attempt['directory_order']if
     row['source']['version9'][:2]==source['version9'][:2])
    require(len(prior)<=1,'INITIAL_STARTUP_ONE_ORIGINAL_PHYSICAL_DIRECTORY')
    if prior:
     prior=prior[0];record['duplicate']=prior
     require(source['version9']==prior['source']['version9']
      and source['flags']==prior['source']['flags']and prior['metadata_complete']is True,
      'INITIAL_STARTUP_REJOIN_DEDUP_ORIGINAL_DIRECTORY')
     record.update(baseline=prior['baseline'],ordinal=prior['ordinal'],names=prior['names'],
      roster=prior['roster'],members=prior['members'],metadata_complete=True)
     record['original']=(record,attempt,binding,source,prior,prior['original'])
    else:
     require(len(attempt['directory_order'])+len(attempt['files'])<16380,
      'INITIAL_STARTUP_ORIGINAL_JOINT_C_DIRECTORY_DOMAIN')
     attempt['directory_order'].append(record)
     baseline=opened(control/('directory'+str(ordinal)));record['baseline']=baseline;protected(baseline,baseline=True)
     iterator=call('INITIAL_STARTUP_ROSTER_OPEN',_f.os.scandir,source['returned_fd'])
     while True:
      try:entry=call('INITIAL_STARTUP_ROSTER_NEXT',next,iterator)
      except StopIteration:break
      name=_f.os.fsencode(entry.name)
      require(name and len(name)<=255 and name not in (b'.',b'..')
       and not any(c in name for c in (0,10,13,47)) and len(names)<65535//2,
       'INITIAL_STARTUP_ORIGINAL_ROSTER_MEMBER')
      names.append(name)
     _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True)
     iterator.close();iterator=None
     names.sort();require(len(set(names))==len(names),'INITIAL_STARTUP_DISTINCT_ROSTER')
     roster=b''.join(name+b'\n'for name in names)
     require(len(roster)<=65535 and baseline['version9'][6]==len(roster),
      'INITIAL_STARTUP_ORIGINAL_ROSTER_EXTENT')
     record['names']=tuple(names);record['roster']=roster;record['ordinal']=ordinal
     rejoin(source,directory=True,protected=True);rejoin(baseline,protected=True)
     for name in names:
      child=_f.Path(_ordinary_ci_initial_path_stock_v1(native_input,str(source_path)+'/'+_f.os.fsdecode(name)))
      info=call('INITIAL_STARTUP_CHILD_NOFOLLOW',_f.os.stat,_f.os.fsdecode(name),dir_fd=source['returned_fd'],follow_symlinks=False)
      version=v9(info);kind=_f.stat.S_IFMT(info.st_mode)
      record['members'].append((name,version,kind))
      if _f.stat.S_ISLNK(info.st_mode):
       target=call('INITIAL_STARTUP_ALIAS_TARGET',_f.os.readlink,child)
       require(v9(call('INITIAL_STARTUP_ALIAS_REJOIN',_f.os.lstat,child))==version,
        'INITIAL_STARTUP_SAME_ORIGINAL_ALIAS_GENERATION')
       attempt['aliases'].append((str(child),target,version))
      else:require(_f.stat.S_ISDIR(info.st_mode)or _f.stat.S_ISREG(info.st_mode),
       'INITIAL_STARTUP_SUPPORTED_ORIGINAL_CHILD_KIND')
     rejoin(source,directory=True,protected=True)
     record['original']=(record,attempt,binding,source,baseline,source['version9'],baseline['version9'])
     record['metadata_complete']=True
   except BaseException as error:failures.append(error)
   finally:
    if iterator is not None:
     try:
      _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True);iterator.close()
     except BaseException as error:failures.append(error)
    dispose(baseline,failures);dispose(source,failures)
   _f._scan_raise_errors(failures)
   if recurse and record['duplicate']is None:
    for name,version,kind in record['members']:
     child=_f.Path(_ordinary_ci_initial_path_stock_v1(native_input,str(source_path)+'/'+_f.os.fsdecode(name)))
     if kind==_f.stat.S_IFDIR:directory(child,depth+1,True)
     elif kind==_f.stat.S_IFREG:compare_file(child,len(attempt['file_order']))
   info=call('INITIAL_STARTUP_DIRECTORY_FINAL_PATH',_f.os.lstat,source_path)
   require(v9(info)==record['source']['version9'],'INITIAL_STARTUP_ORIGINAL_DIRECTORY_FINAL_GENERATION')
  def canonical(value):
   selected=str(path(value))
   for hop in range(40):
    changed=False
    for observed,target,version in attempt['aliases']:
     if selected==observed or selected.startswith(observed+'/'):
      require(v9(call('INITIAL_STARTUP_ALIAS_CURRENT',_f.os.lstat,observed))==version
       and call('INITIAL_STARTUP_ALIAS_TARGET_CURRENT',_f.os.readlink,observed)==target,
       'INITIAL_STARTUP_ORIGINAL_ALIAS_STILL_HELD')
      base=target if target.startswith('/')else str(_f.Path(observed).parent)+'/'+target
      selected=_f.os.path.normpath(base)+selected[len(observed):];path(selected)
      require(_f.Path(selected).is_relative_to(install),'INITIAL_STARTUP_ALIAS_INSIDE_ORIGINAL_INSTALLATION')
      changed=True;break
    if not changed:return selected
   raise ValueError('INITIAL_STARTUP_ALIAS_CHAIN_DOMAIN')
  directory(install,0,True);directory(_f.Path(workspace),0,False);directory(_f.Path(workspace)/'tools',0,False)
  a['environment']=env;a['installation_root']=install;a['control_root_path']=control
  a['control_root_version9']=control_slot['version9']
  for row in attempt['directory_order']:
   baseline=None;failures=[]
   try:
    baseline=opened(control/('directory'+str(row['ordinal'])))
    protected(baseline,baseline=True)
    require(baseline['version9']==row['baseline']['version9']and baseline['flags']==row['baseline']['flags'],
     'INITIAL_STARTUP_SAME_ORIGINAL_ROSTER_BASELINE')
    raw=full(baseline,len(row['roster']))
    require(raw==row['roster'],'INITIAL_STARTUP_EXACT_INDEPENDENT_DIRECTORY_ROSTER_BYTES')
    row['expected_roster']=raw;row['roster_complete']=True
   except BaseException as error:failures.append(error)
   finally:
    if baseline is not None and not baseline['close_attempted']:
     try:close(baseline)
     except BaseException as error:failures.append(error)
   _f._scan_raise_errors(failures)
  require(len(attempt['file_order'])+len(attempt['directory_order'])<=16380,
   'INITIAL_STARTUP_ORIGINAL_C_COMMAND_ROSTER_DOMAIN')
  # The existing fixed C owner captures the entire catalogue before its
  # once-only PROVISION gate. Join its actual immutable Source/body/SO now;
  # names/numbers alone are DATA and cannot establish that predecessor.
  fixed_root=path(temp+'/'+stem+'inputs')
  fixed=opened(fixed_root,True)
  try:
   protected(fixed,True)
   names=[];iterator=call('INITIAL_STARTUP_INPUT4_ROSTER',_f.os.scandir,fixed['returned_fd'])
   a['iterators'].append(iterator)
   try:
    while True:
     try:item=call('INITIAL_STARTUP_INPUT4_NEXT',next,iterator)
     except StopIteration:break
     require(len(names)<8,'INITIAL_STARTUP_EXACT_INPUT4_ROSTER_BOUND');names.append(item.name)
   finally:call('ONE_CLOSE',iterator.close,settling=True)
   require(tuple(sorted(names))==tuple('input'+str(i)for i in range(8)),
    'INITIAL_STARTUP_EXACT_ORIGINAL_INPUT4_NAMES')
   rejoin(fixed,directory=True,protected=True)
   source_ci=readonly_raw(generation['expected_module_closure'][3],fixed_root/'input4',2097152)
   source_workflow=readonly_raw(generation['workflow'],fixed_root/'input0',500000)
  finally:close(fixed)
  ci_module=_f.sys.modules['tools.ci_branch_context'];ci_namespace=ci_module.__dict__
  require(ci_namespace.get('_facet_fn_initial_startup_prebind_v1')is _facet_fn_initial_startup_prebind_v1
   and _facet_fn_initial_startup_prebind_v1.__globals__ is ci_namespace,
   'INITIAL_STARTUP_SAME_FIXED_CI_SOURCE_OWNER')
  ci_code=ci_namespace.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')
  require(type(ci_code)is type(_facet_fn_initial_startup_prebind_v1.__code__)
   and ci_code.co_name=='<module>'and _f.Path(ci_code.co_filename)==generation['expected_module_closure'][3],
   'INITIAL_STARTUP_REAL_INITIALIZED_CI_SOURCE_ROOT')
  compiled=call('INITIAL_STARTUP_SOURCE_COMPILE',compile,source_ci['raw'],ci_code.co_filename,
   'exec',flags=0,dont_inherit=True,optimize=0)
  require(call('INITIAL_STARTUP_SOURCE_CODE_COMPARE',_f._ordinary_control_code_source_equal_v1,
   compiled,ci_code),'INITIAL_STARTUP_SAME_COMPLETE_CI_SOURCE_CODE')
  a['ci_source_code_original']=(a,ci_module,ci_namespace,ci_code,compiled,source_ci,
   _facet_fn_initial_startup_prebind_v1,_facet_fn_initial_startup_prebind_v1.__code__)
  _ordinary_ci_initial_common_source_check_v1(native_input,native_input['early_profile'],native_input['early_allocation_original'])
  # The fixed plaintext literal is extracted as Source DATA. It is not
  # evaluated/imported and never supplies a child-chosen code provider.
  c_template=None
  first_data=b'# QTT_ORDINARY_NATIVE_C_DATA_BEGIN_20261008_V1\n'
  last_data=b'# QTT_ORDINARY_NATIVE_C_DATA_END_20261008_V1\n'
  opening=b"_QTT_ORDINARY_NATIVE_C_SOURCE_V1 = rb'''"
  ci_raw=source_ci['raw']
  require(ci_raw.count(first_data)==ci_raw.count(last_data)==1,
   'INITIAL_STARTUP_ONE_ORIGINAL_C_DATA_FRAME')
  lo=ci_raw.index(first_data)+len(first_data);hi=ci_raw.index(last_data)
  data=ci_raw[lo:hi]
  require(data.startswith(opening)and data.endswith(b"'''\n")and len(data)>len(opening)+4,
   'INITIAL_STARTUP_EXACT_LITERAL_C_DATA_SYNTAX')
  c_template=data[len(opening):-4]
  require(c_template.isascii()and b'\0'not in c_template and b'\r'not in c_template
   and b"'''"not in c_template,'INITIAL_STARTUP_UNENCODED_C_DATA_LITERAL')
  require(type(c_template)is bytes and c_template.endswith(b'\n'),
   'INITIAL_STARTUP_COMPLETE_FIXED_C_SOURCE_LITERAL')
  ordinal=len(attempt['file_order']);code6=tuple(str(value)for value in generation['expected_module_closure'])
  native_c=control/'ordinary-native.c';body=control/'controller.bash';so=control/'ordinary-native.so'
  sources=tuple((selected,ordinal+6+index)for index,selected in enumerate((generation['workflow'],body,native_c,so)))
  pair_c=readonly_raw(native_c,control/('file'+str(ordinal+8)))
  pair_body=readonly_raw(body,control/('file'+str(ordinal+7)))
  pair_so=readonly_raw(so,control/('file'+str(ordinal+9)))
  generated=pair_c['raw'];begin=b'/* QTT_ORIGINAL_COMPILER_OPERANDS_BEGIN_V1 */\n'
  end=b'/* QTT_ORIGINAL_COMPILER_OPERANDS_END_V1 */\n'
  require(generated.startswith(c_template)and generated.count(begin)==1 and generated.count(end)==1
   and generated[len(c_template):].startswith(begin)and generated.endswith(end),
   'INITIAL_STARTUP_SAME_REVIEWED_C_PRODUCT_SOURCE_FRAME')
  numeric=('CALLS','READ_BYTES','METADATA_CALLS','NATIVE_SLOT_COUNT','STORAGE_BYTES','WRITE_BYTES',
   'RETAINED_HEAP_BYTES','REALLOC_ATTEMPT_BYTES','INPUT_COUNT','CATALOGUE_COUNT','ALIAS_COUNT',
   'ABSENCE_COUNT','COMMAND_COUNT','SNAPSHOT_PRIOR_DEV','SNAPSHOT_PRIOR_INO','SNAPSHOT_PRIOR_MODE',
   'SNAPSHOT_PRIOR_UID','SNAPSHOT_PRIOR_GID')
  strings=('INSTALLATION_ROOT','WORKSPACE','SNAPSHOT_ROOT','POLICY_BASE','POLICY_CONFIG',
   'POLICY_FEATURES','POLICY_OUTPUT_ROOT','APPARMOR_PARSER','WORKFLOW_PATH','BASH_CONTROLLER_PATH',
   'NATIVE_C_PATH','NATIVE_SO_PATH','BASH_VERSION')
  values={};rendered=[begin];cursor=len(c_template)+len(begin)
  for leaf in numeric+strings:
   name='QN_SOURCE_'+leaf;retained='QTT_ORIGINAL_'+name
   left=('#ifndef '+name+'\n#error Missing original compiler operand\n#endif\n#define '+retained+' ').encode('ascii')
   right=('\n#if '+name+' != '+retained+'\n#error Original compiler integer disagreement\n#endif\n').encode('ascii')if leaf in numeric else ('\n_Static_assert(sizeof('+name+')==sizeof('+retained+') && __builtin_strcmp('+name+','+retained+')==0,"Original compiler string agreement");\n').encode('ascii')
   width=23 if leaf in numeric else 8192
   require(generated[cursor:cursor+len(left)]==left,'INITIAL_STARTUP_FIXED_ORIGINAL_MACRO_LEFT')
   cursor+=len(left);field=generated[cursor:cursor+width];cursor+=width
   require(len(field)==width and generated[cursor:cursor+len(right)]==right,
    'INITIAL_STARTUP_FIXED_ORIGINAL_MACRO_RIGHT');cursor+=len(right)
   token=field.rstrip(b' ');require(field==token.ljust(width,b' '),'INITIAL_STARTUP_CANONICAL_MACRO_PADDING')
   if leaf in numeric:
    require(token.endswith(b'ULL')and token[:-3].isdigit()and 1<=len(token[:-3])<=20
     and (len(token[:-3])==1 or token[0]!=48),'INITIAL_STARTUP_CANONICAL_ORIGINAL_UINT64')
    value=int(token[:-3]);require(value<(1<<64),'INITIAL_STARTUP_ORIGINAL_UINT64_DOMAIN')
   else:
    require(token.startswith(b'"')and token.endswith(b'"')and 3<=len(token)<=8192,
     'INITIAL_STARTUP_ORIGINAL_STRING_TOKEN')
    pieces=[];at=1
    while at<len(token)-1:
     character=token[at]
     if character==92:
      at+=1;require(at<len(token)-1 and token[at]in(34,92),'INITIAL_STARTUP_STRING_ESCAPE');character=token[at]
     else:require(character!=34,'INITIAL_STARTUP_NO_UNESCAPED_STRING_QUOTE')
     require(32<=character<127,'INITIAL_STARTUP_ORIGINAL_ASCII_STRING');pieces.append(chr(character));at+=1
    value=''.join(pieces)
    require(token==('"'+value.replace('\\','\\\\').replace('"','\\"')+'"').encode('ascii'),
     'INITIAL_STARTUP_CANONICAL_ORIGINAL_STRING')
   values[leaf]=value;rendered.append(left+field+right)
  rendered.append(end)
  require(cursor+len(end)==len(generated)and generated==c_template+b''.join(rendered),
   'INITIAL_STARTUP_EXACT_COMPLETE_PRODUCT_AND_DECLARATIONS')
  expected_paths=dict(INSTALLATION_ROOT=str(install),WORKSPACE=workspace,SNAPSHOT_ROOT=str(control),
   WORKFLOW_PATH=str(generation['workflow']),BASH_CONTROLLER_PATH=str(body),NATIVE_C_PATH=str(native_c),
   NATIVE_SO_PATH=str(so))
  require(all(values[name]==value for name,value in expected_paths.items())
   and values['SNAPSHOT_PRIOR_DEV']==ci.st_dev and values['SNAPSHOT_PRIOR_INO']==ci.st_ino
   and values['SNAPSHOT_PRIOR_MODE']==_f.stat.S_IFDIR|0o700
   and values['SNAPSHOT_PRIOR_UID']==values['SNAPSHOT_PRIOR_GID']==ci.st_uid==ci.st_gid==0
   and values['COMMAND_COUNT']==16+4*values['INPUT_COUNT']+4*values['CATALOGUE_COUNT']<=65536
   and ordinal+13<=values['INPUT_COUNT']<=120000
   and len(attempt['directory_order'])<=values['CATALOGUE_COUNT']<=20000
   and values['METADATA_CALLS']<=values['CALLS']and all(values[key]>0 for key in
    ('CALLS','READ_BYTES','METADATA_CALLS','NATIVE_SLOT_COUNT','STORAGE_BYTES','WRITE_BYTES','RETAINED_HEAP_BYTES','REALLOC_ATTEMPT_BYTES')),
   'INITIAL_STARTUP_ACTUAL_SAME_C_ROOT_AND_SOURCE_BOUNDS')
  for key in('POLICY_BASE','POLICY_CONFIG','POLICY_FEATURES','POLICY_OUTPUT_ROOT'):
   require(path(values[key]).parent==control,'INITIAL_STARTUP_EXACT_OWNED_POLICY_OPERAND')
  require(path(values['APPARMOR_PARSER']).is_absolute()and values['BASH_VERSION']
   and values['BASH_VERSION'].isascii(),'INITIAL_STARTUP_ORIGINAL_FIXED_HOST_OPERANDS')
  expected_backings=tuple('file'+str(i)for i in range(ordinal+13))
  expected_directories=tuple('directory'+str(i)for i in range(len(attempt['directory_order'])))
  iterator=call('INITIAL_STARTUP_COMPLETE_C_ROSTER',_f.os.scandir,control_slot['returned_fd'])
  actual_files=[];actual_dirs=[];control_members=[]
  try:
   while True:
    try:item=call('INITIAL_STARTUP_COMPLETE_C_NEXT',next,iterator)
    except StopIteration:break
    require(len(control_members)<values['INPUT_COUNT']+values['CATALOGUE_COUNT']+16,
     'INITIAL_STARTUP_COMPLETE_C_ROSTER_DOMAIN');control_members.append(item.name)
    if item.name.startswith('file'):actual_files.append(item.name)
    elif item.name.startswith('directory'):actual_dirs.append(item.name)
  finally:call('ONE_CLOSE',iterator.close,settling=True)
  require(set(actual_files)==set(expected_backings)and len(actual_files)==len(expected_backings)
   and set(actual_dirs)==set(expected_directories)and len(actual_dirs)==len(expected_directories),
   'INITIAL_STARTUP_ACTUAL_CONTIGUOUS_ORIGINAL_C_BACKINGS_NO_HOLES_OR_EXTRAS')
  expected_members=(*expected_backings,*expected_directories,native_c.name,body.name,so.name,
   'ordinary-native.baseline.so',*(path(values[key]).name for key in
   ('POLICY_BASE','POLICY_CONFIG','POLICY_FEATURES','POLICY_OUTPUT_ROOT')))
  require(len(set(expected_members))==len(expected_members)and len(control_members)==len(expected_members)
   and set(control_members)==set(expected_members),'INITIAL_STARTUP_EXACT_COMPLETE_OWNED_CONTROL_NAMESPACE')
  # Actual fixed holder command/body and mapped SO join the same living
  # kernel holder observed by original_prebind; a filename is not a receipt.
  holder=origin['holder'];holder_pid=holder[0]
  command=bounded_proc('/proc/'+str(holder_pid)+'/cmdline',65536)
  require(command==b'/usr/bin/bash\0--noprofile\0--norc\0'+_f.os.fsencode(body)+b'\0',
   'INITIAL_STARTUP_SAME_ACTUAL_CONTROLLER_BODY')
  if origin['role']=='PROVISION':
   loan=origin['keeper_observation_loans'];loan_original=loan['original'];slot=loan['roles']['KEEPER_MAPS']
   loan_fields=('native_input','prebind','prebind_original','source_anchor','holder','root','owner','errors',
    'producer','producer_code','module_namespace','initializer_code','slots','observations','roles')
   for selected_role in('CGROUP_NAMESPACE','MOUNT_NAMESPACE','KEEPER_MAPS'):
    retained=loan['roles'][selected_role];slot_original=retained['original']
    expected_slot=(retained,loan,origin,holder,retained['returned_fd'],retained['handle_version'],
     retained['flags'],retained['role'],owner,errors)
    require(type(retained)is dict and retained['role']==selected_role
     and type(slot_original)is tuple and len(slot_original)==10
     and all(left is right for left,right in zip(slot_original,expected_slot)),
     'INITIAL_STARTUP_SAME_ORIGINAL_KEEPER_LOAN_SLOT')
   require(loan['complete']is True and type(loan_original)is tuple and len(loan_original)==16
    and loan_original[0]is loan and all(loan_original[i+1]is loan[name]for i,name in enumerate(loan_fields))
    and loan_original[1]is native_input and loan_original[2]is origin and loan_original[3]is origin['original']
    and loan_original[4]is native_input['preloader_source_anchor']and loan_original[5]is holder
    and loan['producer']is _facet_fn_initial_keeper_observation_loans_v1
    and loan['producer_code']is loan['producer'].__code__ and loan['module_namespace']is globals()
    and loan['initializer_code']is ci_code and any(code is loan['producer_code']for code in ci_code.co_consts)
    and loan['owner']is owner and loan['errors']is errors and loan['product_association']is None
    and len(loan['slots'])==3 and set(loan['roles'])=={'CGROUP_NAMESPACE','MOUNT_NAMESPACE','KEEPER_MAPS'}
    and any(owned is slot for owned in origin['slots'])and slot['source_loan']is loan and slot['held']and not slot['closed']
    and slot['noninherit_returned']and slot['path']==_f.Path('/proc')/str(holder_pid)/'maps'
    and _f._preflight_stamp_v1(call('INITIAL_STARTUP_KEEPER_LOAN_METADATA',_f.os.fstat,
     slot['returned_fd']))==slot['handle_version']
    and not call('INITIAL_STARTUP_KEEPER_LOAN_INHERITANCE',_f.os.get_inheritable,slot['returned_fd'])
    and call('INITIAL_STARTUP_KEEPER_LOAN_CURSOR',_f.os.lseek,slot['returned_fd'],0,_f.os.SEEK_CUR)==0,
    'INITIAL_STARTUP_AUTHENTIC_ORIGINAL_KEEPER_MAPS_LOAN')
   note=dict(slot=slot,prefix=bytearray(),raw=None,complete=False,errors=[]);a['reads'].append(note)
   while True:
    request=_f._ordinary_initial_native_quantum_v1(native_input,min(65536,1048577-len(note['prefix'])))
    raw=call('INITIAL_STARTUP_KEEPER_LOAN_READ',_f.os.read,slot['returned_fd'],request)
    delivered(raw,request,'INITIAL_STARTUP_RETURNED_BYTES');note['prefix'].extend(raw)
    require(len(note['prefix'])<=1048576,'INITIAL_STARTUP_KEEPER_LOAN_MAPS_OVERFLOW')
    if not raw:break
   require(_f._preflight_stamp_v1(call('INITIAL_STARTUP_KEEPER_LOAN_AFTER_HANDLE',_f.os.fstat,
    slot['returned_fd']))==slot['handle_version']
    and _f._preflight_stamp_v1(call('INITIAL_STARTUP_KEEPER_LOAN_AFTER_PATH',_f.os.lstat,
     slot['path']))==slot['path_version']and not call('INITIAL_STARTUP_KEEPER_LOAN_AFTER_INHERITANCE',
     _f.os.get_inheritable,slot['returned_fd']),
    'INITIAL_STARTUP_COMPLETE_SAME_ORIGINAL_AUTHORIZED_KEEPER_MAPS_FD')
   note['raw']=maps=bytes(note['prefix']);note['complete']=True
  else:maps=bounded_proc('/proc/'+str(holder_pid)+'/maps',1048576)
  require(maps.endswith(b'\n'),'INITIAL_STARTUP_COMPLETE_ORIGINAL_KEEPER_MAPS')
  _f._ordinary_initial_native_debit_v1(native_input,'INITIAL_STARTUP_ORIGINAL_MAP_PARSER_IMPORT')
  from tools.validation_scope_registry import _ordinary_runtime7_map_line_registry_v1 as parse_map
  mappings=tuple(call('INITIAL_STARTUP_ORIGINAL_MAP_LINE',parse_map,line)for line in maps.splitlines())
  source_identity=pair_so['source']['version9'][:2]
  matched=tuple(row for row in mappings if row[6]==source_identity[1]
   and row[4:6]==(_f.os.major(source_identity[0]),_f.os.minor(source_identity[0]))
   )
  require(matched and any(row[2][2:3]==b'x'for row in matched)
   and all(row[2][3:4]==b'p'for row in matched),
   'INITIAL_STARTUP_ACTUAL_KEEPER_EXECUTABLE_SAME_SO_MAPPING')
  # The controller is the exact protected Source projection, with only the
  # already selected init fields and immutable phase/SO literals replaced.
  first=b'# QTT_ORIGINAL_CONTROLLER_HELPERS_BEGIN_20261007_V1\n'
  last=b'# QTT_ORIGINAL_CONTROLLER_HELPERS_END_20261007_V1\n';tag=b'# QTT_CTL | '
  lines=source_workflow['raw'].splitlines(keepends=True)
  starts=tuple(i for i,line in enumerate(lines)if line==first);ends=tuple(i for i,line in enumerate(lines)if line==last)
  require(len(starts)==len(ends)==1 and starts[0]<ends[0],
   'INITIAL_STARTUP_EXACT_ORIGINAL_CONTROLLER_SOURCE_FRAME')
  projected=[]
  for line in lines[starts[0]+1:ends[0]]:
   require(line.startswith(tag)and line.endswith(b'\n'),'INITIAL_STARTUP_CONTROLLER_SOURCE_PREFIX');projected.append(line[len(tag):])
  template=b''.join(projected)
  init_before=(b'qtt_ordinary_native init "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" "$qtt_phase_ordinal" \\\n' b'    "$1" "$2" "$3" "$4"')
  phase=native_input['entry_attempt']['phase'];phase_ordinal=generation['runner'].ORDERED_PHASES.index(phase)+1
  init_values=(run,attempt_name,str(phase_ordinal),str(origin['origin_ns']),
   str(values['CALLS']),str(values['READ_BYTES']),str(values['METADATA_CALLS']))
  require(template.count(init_before)==1,'INITIAL_STARTUP_ONE_ORIGINAL_INIT_PROJECTION')
  projected=template.replace(init_before,b'qtt_ordinary_native init '+b' '.join(value.encode('ascii')for value in init_values))
  for marker,value in((b'__QTT_NATIVE_SO_PATH__',str(so)),(b'__QTT_SELECTED_PHASE__',phase),(b'__QTT_SELECTED_ORDINAL__',str(phase_ordinal))):
   require(projected.count(marker)==1,'INITIAL_STARTUP_ONE_ORIGINAL_CONTROLLER_LITERAL')
   projected=projected.replace(marker,("'"+value.replace("'","'\"'\"'")+"'").encode('ascii'))
  require(projected==pair_body['raw'],'INITIAL_STARTUP_EXACT_ORIGINAL_CONTROLLER_BODY_BYTES')
  holder_stat=bounded_proc('/proc/'+str(holder_pid)+'/stat',65536)
  holder_group=bounded_proc('/proc/'+str(holder_pid)+'/cgroup',65536)
  holder_label=bounded_proc('/proc/'+str(holder_pid)+'/attr/current',65536)
  require(_f._ordinary_initial_actor_stat_v1(holder_stat,holder_pid)==holder
   and holder_group==('0::'+operands['holder_cgroup']+'\n').encode('ascii')
   and holder_label==(stem+'controller (enforce)\n').encode('ascii'),
   'INITIAL_STARTUP_SAME_FINAL_LIVING_KEEPER_CREATION_ROLE_AND_LABEL')
  a['keeper_final_original']=(a,holder,holder_stat,holder_group,holder_label,origin_original)
  physical_live();rejoin(control_slot,directory=True)
  a['product_original']=(a,origin,origin_original,control_slot,ci,source_ci,source_workflow,
   pair_c,pair_body,pair_so,c_template,generated,values,tuple(expected_backings),
   tuple(expected_directories),holder,command,maps,mappings,matched,projected,errors)
  if origin['role']=='PROVISION':
   for name,role,kind in(('cgroup','CGROUP_NAMESPACE',0x02000000),('mnt','MOUNT_NAMESPACE',0x00020000)):
    namespace_slot=loan['roles'][role];observed=call('INITIAL_STARTUP_KEEPER_NAMESPACE_HANDLE',
     _f.os.fstat,namespace_slot['returned_fd'])
    actual=call('INITIAL_STARTUP_KEEPER_NAMESPACE_CURRENT',_f.os.stat,'/proc/'+str(owner[0])+'/ns/'+name)
    require(namespace_slot['source_loan']is loan and namespace_slot['role']==role
     and namespace_slot['namespace_type']==kind and namespace_slot['noninherit_returned']
     and any(owned is namespace_slot for owned in origin['slots'])and not namespace_slot['closed']
     and _f._preflight_stamp_v1(observed)==namespace_slot['handle_version']
     and (observed.st_dev,observed.st_ino)==(actual.st_dev,actual.st_ino)
     and not call('INITIAL_STARTUP_KEEPER_NAMESPACE_INHERITANCE',_f.os.get_inheritable,namespace_slot['returned_fd']),
     'INITIAL_STARTUP_SAME_ORIGINAL_PINNED_NAMESPACE_BEFORE_CONSTRUCTOR')
   loan['product_association']=(loan,a,a['product_original'],a['ci_source_code_original'],
    origin_original,control_slot,pair_c,pair_body,pair_so,holder,maps,matched,errors)
  attempt.update(metadata_complete=True,product_original=a['product_original'],complete=False)
  a.update(startup_attempt=attempt,compiler_values=values,complete=True)
  a['success_original']=(a,a['original'],attempt,a['product_original'],a['pending_acl'],
   a['source_pairs'],control_slot,origin_original,native_input['early_allocation_original'],prefix,errors)
  startup['pre_cold_result']=a
  return a
 except BaseException as error:
  if all(error is not old for old in errors):errors.append(error)
  _f._scan_raise_errors(errors)
  raise


def _facet_fn_original_source_input4_rejoin_v1(native_input, physical,
 original_cutoffs, producer, containing_function):
 """Issue the fixed receiver-local readonly Input4 binding after real funding."""
 import tools.validation_reliability as _f
 require=_f._preflight_require_v1
 generation=native_input['source_generation'];errors=native_input['errors']
 owner=native_input['owner'];native=native_input['native_instance']
 original=generation['original']
 po=(native_input,producer,producer.__code__,containing_function,containing_function.__code__)
 require(type(native_input)is dict and owner==(_f.os.getpid(),_f.threading.get_ident())
  and type(errors)is list and not errors and type(original)is tuple and len(original)==17
  and original[0]is generation and original[1]is native_input and original[16]is errors
  and generation['module_namespace']is _f.__dict__ and generation['module']is _f
  and type(po)is tuple and len(po)==5 and po[0]is native_input and po[1]is producer
  and po[2]is producer.__code__ and po[3]is containing_function
  and po[4]is containing_function.__code__
  and containing_function is generation['native_method']
  and po[4]is generation['native_method_code']is original[11]
  and original[10]is containing_function
  and _f._LinuxSourceNativeV2.__dict__['_ordinary_initial_native_product_v1'].__func__ is containing_function
  and producer.__name__=='_original_source_input4_rejoin_v1'
  and producer.__globals__ is containing_function.__globals__ is _f.__dict__
  and any(code is po[2]for code in po[4].co_consts)
  and type(native)is _f._LinuxSourceNativeV2 and native_input['native_init_returned']is True,
  'INPUT4_LOCAL_ORIGINAL_NESTED_PRODUCER')
 require('source_input4_producer_original'not in native_input,'INPUT4_LOCAL_ONE_PRODUCER_ORIGINAL')
 native_input['source_input4_producer_original']=po
 frame=_f.sys._getframe(1)
 try:
  require(frame.f_code is po[2]and frame.f_globals is _f.__dict__
   and frame.f_locals.get('native_input')is native_input
   and frame.f_locals.get('physical')is physical
   and frame.f_locals.get('original_cutoffs')is original_cutoffs,
   'INPUT4_LOCAL_ORIGINAL_ACTIVE_PRODUCER_FRAME')
 finally:del frame
 _f._ordinary_initial_preloader_return_check_v1(native_input)
 require(physical is native_input['current_native_observation']
  and physical['native']is native and physical['owner']is owner
  and physical['errors']is errors and physical['complete']is True
  and physical['pending']is False and type(physical['original'])is tuple
  and len(physical['original'])==12 and physical['original'][0]is physical
  and physical['original'][1]is native_input and physical['original'][8]is physical['slots']
  and physical['original'][9]is physical['reads']and physical['original'][11]is physical['operations']
  and type(physical['result_original'])is tuple and len(physical['result_original'])==16
  and physical['result_original'][0]is physical
  and physical['result_original'][1]is physical['original']
  and physical['result_original'][14]is native_input['early_profile']
  and physical['result_original'][15]is errors
  and original_cutoffs is _f._ordinary_initial_prefix_capacity_checked_v1(native_input)['original_cutoffs']
  and original_cutoffs==(physical['origin_ns'],physical['origin_ns']+3500*10**9,
   native_input['original_execution_cutoff_ns'],native_input['original_settlement_cutoff_ns'])
  and generation['protected_inputs']is None and generation['native_input_binding']is None
  and 'source_input4_acquisition'not in generation,
  'INPUT4_LOCAL_AFTER_REAL_PHYSICAL_SINGLE_ISSUANCE')
 operands=physical['operands'];role=operands['role']
 require(role in ('PROVISION','PARENT','RECEIVER'),'INPUT4_LOCAL_ORIGINAL_ROLE')
 rows=[];pairs=[];records=[]
 binding=dict(generation=generation,native_input=native_input,generation_original=original,
  inputs=None,rows=rows,root_slot=None,physical=physical,physical_original=physical['original'],
  physical_result=physical['result_original'],cutoffs=original_cutoffs,role=role,
  producer=producer,producer_code=po[2],containing_function=containing_function,
  containing_code=po[4],errors=errors,complete=False,producer_original=po)
 a=dict(binding=binding,generation=generation,native_input=native_input,producer=producer,
  producer_code=po[2],helper=_facet_fn_original_source_input4_rejoin_v1,
  helper_code=_facet_fn_original_source_input4_rejoin_v1.__code__,records=records,
  aliases=[],operations=[],iterators=[],returned=[],code_observations=[],complete=False,
  errors=errors,result=None)
 generation['source_input4_acquisition']=a
 a['attempt_original']=(a,binding,generation,original,native_input,po,
  physical,physical['original'],physical['result_original'],original_cutoffs,errors)
 def call(label,function,*args,settling=False,**kwargs):
  row=dict(label=label,function=function,args=args,kwargs=kwargs,
   admission_attempted=True,attempted=False,result=None,error=None,settling=settling)
  a['operations'].append(row)
  try:
   _f._ordinary_initial_native_debit_v1(native_input,label,settling=settling)
   row['attempted']=True;row['result']=function(*args,**kwargs);return row['result']
  except BaseException as error:row['error']=error;raise
 def v9(info):
  return(info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid,
   info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
 def v11(info):
  return[info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,
   info.st_ctime_ns,info.st_nlink,info.st_uid,info.st_gid,
   getattr(info,'st_file_attributes',0),getattr(info,'st_reparse_tag',0)]
 def path(value):
  _ordinary_ci_initial_path_stock_v1(native_input,value)
  require(type(value)is str and value.startswith('/')and value!='/'and '\\'not in value
   and not any(c in value for c in ('\0','\n','\r'))
   and len(value.encode('utf-8'))<=4096 and len(value.split('/'))<=65
   and all(part and part not in ('.','..')and len(part.encode('utf-8'))<=255
    for part in value.split('/')[1:]),'INPUT4_LOCAL_FIXED_ABSOLUTE_COMPONENTS')
  return _f.Path(value)
 def close(slot):
  require(not slot['close_admission_attempted']and not slot['close_attempted']
   and not slot['closed']and type(slot['returned_fd'])is int,
   'INPUT4_LOCAL_ORIGINAL_ONE_CLOSE')
  slot['close_admission_attempted']=True
  _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True)
  slot['close_attempted']=True
  try:_f.os.close(slot['returned_fd']);slot['closed']=True
  except BaseException as error:slot['errors'].append(error);raise
 def opened(value,directory=False):
  selected=path(str(value));previous=None
  for index,component in enumerate(('/',*selected.parts[1:])):
   final=index==len(selected.parts)-1
   slot=dict(owner=owner,path=_f.Path('/')if index==0 else previous['path']/component,
    component=component,parent=previous,returned_fd=None,open_attempted=False,
    close_admission_attempted=False,close_attempted=False,closed=False,held=False,errors=[],complete=False)
   physical['slots'].append(slot)
   try:
    args={}if previous is None else dict(dir_fd=previous['returned_fd'])
    before=call('INPUT4_LOCAL_PATH_METADATA',_f.os.stat,component,follow_symlinks=False,**args)
    slot['path_version']=_f._preflight_stamp_v1(before)
    slot['uid'],slot['gid']=before.st_uid,before.st_gid
    require(not _f._stat_is_reparse_point(before)and not _f.stat.S_ISLNK(before.st_mode)
     and (_f.stat.S_ISDIR(before.st_mode)if not final or directory else
      _f.stat.S_ISREG(before.st_mode)and before.st_nlink==1),'INPUT4_LOCAL_NOFOLLOW_KIND')
    flags=_f.os.O_RDONLY|_f.os.O_NOFOLLOW|_f.os.O_CLOEXEC|_f.os.O_NONBLOCK
    if not final or directory:flags|=_f.os.O_DIRECTORY
    _f._ordinary_initial_native_debit_v1(native_input,'INPUT4_LOCAL_COMPONENT_OPEN')
    slot['open_attempted']=True;slot['returned_fd']=_f.os.open(component,flags,**args)
    held=call('INPUT4_LOCAL_HANDLE_METADATA',_f.os.fstat,slot['returned_fd'])
    after=call('INPUT4_LOCAL_PATH_REJOIN',_f.os.stat,component,follow_symlinks=False,**args)
    require(v11(before)==v11(held)==v11(after)
     and not call('INPUT4_LOCAL_INHERITANCE',_f.os.get_inheritable,slot['returned_fd']),
     'INPUT4_LOCAL_COMPLETE_PATH_HANDLE_GENERATION')
    slot['handle_version']=_f._preflight_stamp_v1(held)
    slot['version']=v11(held);slot['version9']=v9(held)
    if previous is not None:close(previous)
    previous=slot
   except BaseException as error:slot['errors'].append(error);raise
  slot['held']=True;return slot
 def rejoin(slot,directory=False,protected=False):
  require(slot['owner']is owner and not slot['close_admission_attempted']
   and not slot['close_attempted']and not slot['closed'],
   'INPUT4_LOCAL_RETAINED_ORIGINAL_DESCRIPTOR')
  held=call('INPUT4_LOCAL_HELD_REJOIN',_f.os.fstat,slot['returned_fd'])
  named=call('INPUT4_LOCAL_NAMED_REJOIN',_f.os.lstat,slot['path'])
  require(v11(held)==v11(named)==slot['version']and v9(held)==slot['version9']
   and not _f._stat_is_reparse_point(named)and not _f.stat.S_ISLNK(named.st_mode)
   and (_f.stat.S_ISDIR(held.st_mode)if directory else
    _f.stat.S_ISREG(held.st_mode)and held.st_nlink==1)
   and not call('INPUT4_LOCAL_HELD_INHERITANCE',_f.os.get_inheritable,slot['returned_fd']),
   'INPUT4_LOCAL_UNCHANGED_COMPLETE_CURRENT_GENERATION')
  parent=slot['parent']
  while parent is not None:
   info=call('INPUT4_LOCAL_ANCESTOR_REJOIN',_f.os.lstat,parent['path'])
   require(_f.stat.S_ISDIR(info.st_mode)and not _f._stat_is_reparse_point(info)
    and (info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid)
     ==(*parent['path_version'][:3],parent['uid'],parent['gid']),
     'INPUT4_LOCAL_UNCHANGED_NOFOLLOW_ANCESTRY')
   parent=parent['parent']
  if protected:
   require(call('INPUT4_LOCAL_PROTECTED_FLAGS',native.flags,slot['returned_fd'])==slot['flags'],
    'INPUT4_LOCAL_SAME_PROTECTED_FLAGS')
  return held
 def delivered(raw,request,label):
  note=dict(raw=raw,request_bytes=request,label=label,debited=False)
  a['returned'].append(note)
  _f._ordinary_initial_native_debit_v1(native_input,label,raw=raw,request_bytes=request)
  note['debited']=True
 def full(slot,extent):
  require(type(extent)is int and 0<=extent<=134217728,'INPUT4_LOCAL_ORIGINAL_FILE128_DOMAIN')
  attempt=dict(complete=True)
  slot.update(prefix=bytearray(),last_returned=None,returned_bytes=0,raw=None,complete=False,
   read_attempt=attempt,read_attempts=0,read_admission_attempts=0,read_admitted_calls=0,
   read_native_attempts=0,read_bytes_debited=0,successful_reads=0,successful_bytes=0,eof_observed=False)
  physical['reads'].append(slot)
  call('INPUT4_LOCAL_REWIND',_f.os.lseek,slot['returned_fd'],0,_f.os.SEEK_SET)
  def acquire(desired,eof):
   require(attempt['complete']is True,'INPUT4_LOCAL_PREVIOUS_READ_COMMITTED')
   # ONE slot-local attempt survives until its actual delivery commits.
   # Successful advances overwrite it; the original shared debit ledger persists.
   attempt.clear();attempt.update(label='INPUT4_LOCAL_EOF'if eof else'INPUT4_LOCAL_READ',
    desired=desired,request=None,quantum_attempted=True,admission_attempted=False,
    attempted=False,result=None,byte_admission_attempted=False,debited=False,
    eof=eof,complete=False,error=None)
   slot['read_attempts']+=1
   try:
    request=_f._ordinary_initial_native_quantum_v1(native_input,desired)
    attempt['request']=request;attempt['admission_attempted']=True
    slot['read_admission_attempts']+=1
    _f._ordinary_initial_native_debit_v1(native_input,attempt['label'])
    slot['read_admitted_calls']+=1;attempt['attempted']=True
    slot['read_native_attempts']+=1
    block=_f.os.read(slot['returned_fd'],request)
    attempt['result']=slot['last_returned']=block
    slot['returned_bytes']+=len(block);attempt['byte_admission_attempted']=True
    _f._ordinary_initial_native_debit_v1(native_input,'INPUT4_LOCAL_RETURNED_BYTES',
     raw=block,request_bytes=request)
    attempt['debited']=True;slot['read_bytes_debited']+=len(block)
    slot['prefix'].extend(block)
    require((not block and slot['returned_bytes']==extent)if eof else
     (block and slot['returned_bytes']<=extent),
     'INPUT4_LOCAL_EXACT_EOF'if eof else'INPUT4_LOCAL_COMPLETE_PROGRESS')
    slot['successful_reads']+=1;slot['successful_bytes']+=len(block)
    if eof:slot['eof_observed']=True
    attempt['complete']=True
   except BaseException as error:
    attempt['error']=error
    if all(error is not old for old in slot['errors']):slot['errors'].append(error)
    if all(error is not old for old in errors):errors.append(error)
    raise
  while len(slot['prefix'])<extent:acquire(min(65536,extent-len(slot['prefix'])),False)
  acquire(1,True)
  rejoin(slot,protected=True);slot['raw']=bytes(slot['prefix']);slot['complete']=True
  return slot['raw']
 def acl(slot):
  prefix=_f._ordinary_initial_prefix_v1(native_input)
  profile=native_input['early_profile'];allocation=native_input['early_allocation_original']
  # Existing native.acl has one65536 names request and two1028 value requests.
  # Its delivered callback precedes raw retention. Admit the WHOLE fixed
  # synchronous maximum against the SAME remaining pool before first native read.
  require(min(profile[9]-prefix['returned_bytes'],
   allocation[2]['work_bytes']-allocation[3]['work_bytes'])>=65536+2*1028,
   'INPUT4_LOCAL_WHOLE_ACL_MAXIMUM_PROSPECTIVE_ADMISSION')
  counts=[];failure=None;values=None
  note=dict(slot=slot,counts=counts,result=None,last=None,error=None,body_error=None,
   native_failure=None,delivery_error=None,complete=False)
  slot['acl_observation']=note
  def attempted(operation):
   request=65536 if operation=='flistxattr'else 1028
   require(_f._ordinary_initial_native_quantum_v1(native_input,request)==request,
    'INPUT4_LOCAL_ACL_FULL_REQUEST_ADMITTED')
   _f._ordinary_initial_native_debit_v1(native_input,'INPUT4_LOCAL_ACL_'+operation)
  def received(count):
   require(type(count)is int and count>=0,'INPUT4_LOCAL_ACTUAL_ACL_RETURN_COUNT')
   counts.append(count)
  try:values=native.acl(slot['returned_fd'],attempt=attempted,delivered=received)
  except BaseException as error:
   failure=error;note['native_failure']=note['body_error']=error
   if all(error is not old for old in errors):errors.append(error)
  last=native.last_acl;note['last']=last
  try:
   actual=[]
   if type(last.get('names_hex'))is str:
    actual.append((bytes.fromhex(last['names_hex']),65536))
   for item in last.get('values',()):
    if type(item.get('raw_hex'))is str:actual.append((bytes.fromhex(item['raw_hex']),1028))
   for block,request in actual:delivered(block,request,'INPUT4_LOCAL_ACL_RETURNED_BYTES')
   require(len(actual)==len(counts)and all(len(block)==count
    for (block,_),count in zip(actual,counts)),'INPUT4_LOCAL_COMPLETE_ACL_RETURN_CUSTODY')
   if failure is not None:raise failure
   require(values==(None,None),'INPUT4_LOCAL_ORIGINAL_ACL_ABSENCE')
   note['result']=values;note['complete']=True;slot['acl']=values
  except BaseException as error:
   note['error']=error
   if error is not failure:note['delivery_error']=error
   if all(error is not old for old in errors):errors.append(error)
   if failure is not None and error is not failure:_f._scan_raise_errors([failure,error])
   raise
  rejoin(slot,directory=_f.stat.S_ISDIR(slot['version'][2]))
 def protected(slot,directory=False,baseline=False):
  info=rejoin(slot,directory=directory)
  mode=_f.stat.S_IMODE(info.st_mode)
  require(info.st_uid==info.st_gid==0 and mode==(0o555 if directory else 0o444)
   if directory or baseline else info.st_uid==info.st_gid==0 and mode in (0o444,0o555),
   'INPUT4_LOCAL_CURRENT_READONLY_OWNER_MODE')
  slot['flags']=call('INPUT4_LOCAL_FLAGS',native.flags,slot['returned_fd'])
  require(type(slot['flags'])is int and slot['flags']&16,'INPUT4_LOCAL_ACTUAL_IMMUTABLE')
  acl(slot);rejoin(slot,directory=directory,protected=True)
 def roster(slot):
  note=dict(slot=slot,iterator=None,open_attempted=True,close_admission_attempted=False,
   close_attempted=False,closed=False,names=[],complete=False,error=None,close_error=None)
  a['iterators'].append(note)
  try:
   note['iterator']=call('INPUT4_LOCAL_ROSTER_OPEN',_f.os.scandir,slot['returned_fd'])
   while True:
    try:entry=call('INPUT4_LOCAL_ROSTER_NEXT',next,note['iterator'])
    except StopIteration:break
    require(len(note['names'])<8,'INPUT4_LOCAL_EXACT_EIGHT_MEMBER_BOUND')
    note['names'].append(entry.name)
   require(tuple(sorted(note['names']))==tuple('input'+str(i)for i in range(8)),
    'INPUT4_LOCAL_EXACT_BASELINE_ROSTER')
   rejoin(slot,directory=True,protected=True);note['complete']=True
  except BaseException as error:
   note['error']=error
   if all(error is not old for old in errors):errors.append(error)
   raise
  finally:
   if note['iterator']is not None:
    try:
     note['close_admission_attempted']=True
     _f._ordinary_initial_native_debit_v1(native_input,'ONE_CLOSE',settling=True)
     note['close_attempted']=True;note['iterator'].close();note['closed']=True
    except BaseException as error:
     note['close_error']=error
     if all(error is not old for old in errors):errors.append(error)
     if note['error']is not None and note['error']is not error:
      _f._scan_raise_errors([note['error'],error])
     raise
 def resolve_compiler():
  current='/usr/bin/cc'
  for step in range(64):
   selected=path(current);prefix='';changed=False
   for index,component in enumerate(selected.parts[1:]):
    prefix+='/'+component
    before=call('INPUT4_LOCAL_COMPILER_ALIAS_BEFORE',_f.os.lstat,prefix)
    require(not _f._stat_is_reparse_point(before),'INPUT4_LOCAL_COMPILER_NO_REPARSE')
    if _f.stat.S_ISLNK(before.st_mode):
     alias=dict(path=prefix,version=v11(before),target=None,after=None,error=None)
     a['aliases'].append(alias)
     alias['target']=call('INPUT4_LOCAL_COMPILER_ALIAS_READ',_f.os.readlink,prefix)
     after=call('INPUT4_LOCAL_COMPILER_ALIAS_AFTER',_f.os.lstat,prefix);alias['after']=v11(after)
     target=alias['target']
     require(type(target)is str and target and '\0'not in target
      and len(target.encode('utf-8'))<=4096 and alias['version']==alias['after'],
      'INPUT4_LOCAL_COMPILER_ALIAS_GENERATION')
     replacement=target if target.startswith('/')else _f.os.path.dirname(prefix)+'/'+target
     if index+1<len(selected.parts)-1:replacement+='/'+ '/'.join(selected.parts[index+2:])
     current=_f.os.path.normpath(replacement);path(current);changed=True;break
    require(_f.stat.S_ISDIR(before.st_mode)if index+1<len(selected.parts)-1 else
     _f.stat.S_ISREG(before.st_mode),'INPUT4_LOCAL_COMPILER_COMPONENT_KIND')
   if not changed:return current
  raise _f.ValidationReliabilityError('ENGVR_PREFLIGHT_DENIED','INPUT4_COMPILER_ALIAS_DEPTH')
 def code_member(root,code):
  pending=[root];seen=set()
  while pending:
   current=pending.pop()
   if id(current)in seen:continue
   seen.add(id(current))
   if current is code:return True
   pending.extend(x for x in current.co_consts if type(x)is type(root))
  return False
 def bind_code(record,name,witness):
  module=(generation['runner']if record['index']==1 else generation['module']
   if record['index']==2 else _f.sys.modules.get(name))
  require(type(module)is type(_f.sys),'INPUT4_LOCAL_ACTUAL_MODULE_NAMESPACE')
  namespace=module.__dict__;actual_name=namespace.get('__name__')
  require(type(actual_name)is str and _f.sys.modules.get(actual_name)is module,
   'INPUT4_LOCAL_MODULE_REGISTRATION_CONTINUITY')
  filename=record['filename'];relative='tools/'+name.split('.')[-1]+'.py'
  whole=record['index']!=6
  root=namespace.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')if whole else None
  require(type(witness)is type(containing_function)and witness.__globals__ is namespace
   and witness.__module__==actual_name
   and namespace.get('__file__')in (filename,relative),'INPUT4_LOCAL_ORIGINAL_FUNCTION_NAMESPACE')
  if whole:
   require(type(root)is type(containing_function.__code__)and root.co_name=='<module>'
    and root.co_filename in (filename,relative),'INPUT4_LOCAL_REAL_WHOLE_MODULE_INITIALIZER')
   code_filename=root.co_filename
  else:
   require(namespace.get('normalize_repo_ref')is witness
    and witness.__code__.co_filename in (filename,relative),
    'INPUT4_LOCAL_UNCHANGED_REFS_FIXED_FUNCTION_WITNESS')
   code_filename=witness.__code__.co_filename
  require(_f.sys.flags.optimize==0,'INPUT4_LOCAL_ORIGINAL_COMPILE_POLICY')
  note=dict(record=record,module=module,namespace=namespace,root=root,witness=witness,
   filename=code_filename,raw=record['raw'],compiled=None,complete=False,error=None,
   proof_kind='WHOLE_MODULE_INITIALIZER'if whole else 'FIXED_FUNCTION_WITNESS',
   whole_initializer=whole)
  a['code_observations'].append(note)
  try:
   compiled=call('INPUT4_LOCAL_PROTECTED_SOURCE_COMPILE',compile,record['raw'],code_filename,
    'exec',flags=0,dont_inherit=True,optimize=0);note['compiled']=compiled
   if whole:
    require(call('INPUT4_LOCAL_WHOLE_CODE_COMPARE',_f._ordinary_control_code_source_equal_v1,
     compiled,root)and namespace.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')is root
     and code_member(root,witness.__code__),'INPUT4_LOCAL_WHOLE_SOURCE_CODE_JOIN')
   else:
    pending=[compiled];matches=[]
    while pending:
     current=pending.pop()
     if current.co_qualname==witness.__code__.co_qualname:matches.append(current)
     pending.extend(x for x in current.co_consts if type(x)is type(compiled))
    require(len(matches)==1 and call('INPUT4_LOCAL_FIXED_FUNCTION_CODE_COMPARE',
     _f._ordinary_control_code_source_equal_v1,matches[0],witness.__code__)
     and namespace.get('normalize_repo_ref')is witness,
     'INPUT4_LOCAL_PROTECTED_REFS_FUNCTION_SOURCE_JOIN')
   require(_f.sys.modules.get(actual_name)is module and module.__dict__ is namespace
    and witness.__globals__ is namespace,'INPUT4_LOCAL_LIVING_SOURCE_MODULE_CONTINUITY')
   note['original']=(note,record,module,namespace,root,witness,witness.__code__,
    record['raw'],compiled,note['filename'],note['proof_kind'])
   note['complete']=True;record['code_binding']=note
  except BaseException as error:note['error']=error;raise
 def physical_live():
  require(physical is native_input['current_native_observation']and physical['complete']is True
   and physical['original']is binding['physical_original']
   and physical['result_original']is binding['physical_result']and not errors,
   'INPUT4_LOCAL_SAME_PHYSICAL_OWNER')
  select_module=_f.sys.modules.get('select')
  require(type(select_module)is type(_f.sys),'INPUT4_LOCAL_EXISTING_PIDFD_POLL_MODULE')
  slot=physical['holder_pidfd_slot']
  require(slot['held']is True and not slot['close_attempted']and not slot['closed'],
   'INPUT4_LOCAL_ORIGINAL_LIVING_HOLDER_PIDFD')
  poll=call('INPUT4_LOCAL_PIDFD_POLL_CREATE',select_module.poll)
  call('INPUT4_LOCAL_PIDFD_POLL_REGISTER',poll.register,slot['returned_fd'],select_module.POLLIN)
  require(not call('INPUT4_LOCAL_HOLDER_LIVENESS',poll.poll,0),'INPUT4_LOCAL_HOLDER_REMAINS_ALIVE')
  for name in ('ancestor_cgroup','common_cgroup','bootstrap_cgroup','holder_cgroup'):
   slot=physical['held_cgroups'][name]
   require(slot['held']is True and not slot['close_attempted']and not slot['closed'],
    'INPUT4_LOCAL_ORIGINAL_CGROUP_CUSTODY')
   held=call('INPUT4_LOCAL_CGROUP_HANDLE',_f.os.fstat,slot['returned_fd'])
   named=call('INPUT4_LOCAL_CGROUP_PATH',_f.os.lstat,slot['path'])
   require(_f._preflight_stamp_v1(held)==slot['handle_version']
    and _f._preflight_stamp_v1(named)==slot['path_version']
    and _f._same_observed_file(named,held),'INPUT4_LOCAL_ORIGINAL_CGROUP_GENERATION')
  role_root=physical['native_root_slot']
  require(role_root['held']is True and not role_root['close_attempted']
   and not role_root['closed']and role_root['path']==operands['native_root'],
   'INPUT4_LOCAL_SAME_ORIGINAL_NATIVE_ROOT')
  expected=role_root.get('last_output_version',(role_root['path_version'],role_root['handle_version']))
  held=call('INPUT4_LOCAL_NATIVE_ROOT_HANDLE',_f.os.fstat,role_root['returned_fd'])
  named=call('INPUT4_LOCAL_NATIVE_ROOT_PATH',_f.os.lstat,role_root['path'])
  require(_f._preflight_stamp_v1(named)==expected[0]
   and _f._preflight_stamp_v1(held)==expected[1]and _f._same_observed_file(named,held),
   'INPUT4_LOCAL_ORIGINAL_NATIVE_ROOT_GENERATION')
  # The fixed existing physical producer already froze actor membership,
  # manager generations, holder pid/start, kernel controls and original origin.
  # This observer retains those same objects; it creates no replacement grant.
 try:
  physical_live()
  phase=native_input['entry_attempt']['phase']
  phases=('fast-preflight','deterministic-validators-a','deterministic-validators-b',
   'deterministic-validators-c','pytest-shard-1','pytest-shard-2','pytest-shard-3',
   'pytest-shard-4','pytest-shard-5','pytest-shard-6','pytest-shard-7','pytest-shard-8','post-validation')
  require(phase in phases,'INPUT4_LOCAL_FIXED_ORIGINAL_PHASE')
  env=tuple((key,_f.os.environ.get(key))for key in
   ('GITHUB_WORKSPACE','RUNNER_TEMP','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'))
  require(all(type(value)is str and value for _,value in env),'INPUT4_LOCAL_FIXED_ENVIRONMENT_LOCATORS')
  workspace,temp,run,attempt=(value for _,value in env)
  for value in (run,attempt):
   require(value.isascii()and value.isdecimal()and not value.startswith('0')and len(value)<=19,
    'INPUT4_LOCAL_EXACT_RUN_ATTEMPT')
  stem='qtt'+run+'n'+attempt+'p'+str(phases.index(phase)+1)
  require(stem==operands['stem']and str(generation['workflow'])==workspace+
   '/.github/workflows/qtt_validation.yml','INPUT4_LOCAL_SOURCE_ROLE_NAMESPACE_JOIN')
  root=path(temp+'/'+stem+'inputs');repo=path(workspace)
  require(not root.is_relative_to(repo)and not repo.is_relative_to(root)
   and not root.is_relative_to(operands['native_root'])
   and not operands['native_root'].is_relative_to(root),
   'INPUT4_LOCAL_NONOVERLAPPING_ORIGINAL_INPUT_NAMESPACE')
  root_slot=opened(root,True);binding['root_slot']=root_slot
  protected(root_slot,True);roster(root_slot)
  framework=(('workflow',generation['workflow'],None),)+tuple(
   (label,repo/'tools'/filename,module)for label,filename,module in(
    ('run-validation-source','run_validation_gates.py','tools.run_validation_gates'),
    ('reliability-source','validation_reliability.py','tools.validation_reliability'),
    ('scope-registry-source','validation_scope_registry.py','tools.validation_scope_registry'),
    ('branch-context-source','ci_branch_context.py','tools.ci_branch_context'),
    ('inventory-source','validation_inventory.py','tools.validation_inventory'),
    ('repo-path-source','repo_path_refs.py','tools.repo_path_refs')))
  require(tuple(item[1]for item in framework[1:])==(generation['code_paths']+
   (repo/'tools/validation_inventory.py',repo/'tools/repo_path_refs.py')),
   'INPUT4_LOCAL_EXACT_SIX_SOURCE_CLOSURE')
  selected=framework+(('compiler-image',path(resolve_compiler()),None),)
  require(len(selected)==8,'INPUT4_LOCAL_COMPLETE_EIGHT_SOURCE_INPUTS')
  for index,(label,filename,module_name)in enumerate(selected):
   record=dict(role=label,index=index,filename=str(filename),module=module_name,
    source_row=None,baseline_row=None,source_version=None,baseline_version=None,
    input4=None,raw=None,baseline_raw=None,profile=None,error=None,complete=False)
   records.append(record)
   acquisition=dict(binding=binding,record=record,producer=producer,producer_code=po[2],
    source_row=None,baseline_row=None,raw=None,baseline_raw=None,errors=errors,complete=False)
   record['acquisition']=acquisition
   acquisition['attempt_original']=(acquisition,binding,record,producer,po[2],errors)
   try:
    source=opened(filename);record['source_row']=acquisition['source_row']=source
    baseline=opened(root/('input'+str(index)))
    record['baseline_row']=acquisition['baseline_row']=baseline
    protected(source);protected(baseline,baseline=True)
    source_caps=(500000,1048576,2097152,1048576,2097152,2097152,None,None)
    cap=source_caps[index]
    require(cap is None or source['version9'][6]<=cap,'INPUT4_LOCAL_FIXED_SOURCE_EXTENT_DOMAIN')
    require(source['version9'][:2]!=baseline['version9'][:2]
     and source['version9'][6]==baseline['version9'][6],
     'INPUT4_LOCAL_PHYSICALLY_INDEPENDENT_COMPLETE_BASELINE')
    raw=full(source,source['version9'][6]);record['raw']=acquisition['raw']=raw
    expected=full(baseline,baseline['version9'][6]);record['baseline_raw']=acquisition['baseline_raw']=expected
    require(raw==expected,'INPUT4_LOCAL_FULL_SOURCE_BASELINE_BYTES')
    item=(str(filename),source['version9'],str(baseline['path']),baseline['version9'])
    record['input4']=item;record['source_version']=item[1];record['baseline_version']=item[3]
    acquisition['original']=(acquisition,binding,record,producer,po[2],source,baseline,raw,expected,errors)
    record['acquisition_original']=acquisition['original']
    record['original']=(record,generation,binding,item,source,baseline,raw,expected,
     acquisition,acquisition['original'])
    acquisition['complete']=record['complete']=True
    pairs.append((label,item))
    if index<7:rows.append(record)
   except BaseException as error:record['error']=error;raise
  witnesses=(generation['entry'],generation['native_method'],
   _f.sys.modules['tools.validation_scope_registry'].__dict__['_facet_fn_initial_native_observations_v1'],
   _facet_fn_original_source_input4_rejoin_v1,
   _f.sys.modules['tools.validation_inventory'].__dict__['_facet_fn_control_current_profile_literals_v1'],
   _f.sys.modules['tools.repo_path_refs'].__dict__['normalize_repo_ref'])
  for record,witness in zip(records[1:7],witnesses):bind_code(record,record['module'],witness)
  require(records[1]['code_binding']['root']is generation['initializer']
   and records[1]['code_binding']['module']is generation['runner']
   and records[2]['code_binding']['module']is generation['module']
   and generation['native_method'].__code__ is generation['native_method_code']
   and code_member(records[2]['code_binding']['root'],po[4])
   and code_member(po[4],po[2]),'INPUT4_LOCAL_PRELOADER_LIVING_SOURCE_CODE_JOIN')
  for alias in a['aliases']:
   require(v11(call('INPUT4_LOCAL_COMPILER_ALIAS_FINAL',_f.os.lstat,alias['path']))==alias['version']
    and call('INPUT4_LOCAL_COMPILER_ALIAS_TARGET_FINAL',_f.os.readlink,alias['path'])==alias['target'],
    'INPUT4_LOCAL_RETAINED_COMPILER_ALIAS_GENERATIONS')
  for record in records:
   rejoin(record['source_row'],protected=True);rejoin(record['baseline_row'],protected=True)
   require(record['complete']and record['acquisition']['complete'],'INPUT4_LOCAL_EVERY_COMPLETE_PAIR')
  roster(root_slot);physical_live()
  require(env==tuple((key,_f.os.environ.get(key))for key,_ in env)
   and generation['original']is original and len(rows)==7 and len(pairs)==8
   and not errors,'INPUT4_LOCAL_COMPLETE_SAME_ORIGINAL_READONLY_RESULT')
  inputs=tuple(pairs);binding['inputs']=inputs
  root_slot['source_binding_original']=(root_slot,binding,generation,original,native_input,
   physical,physical['original'],physical['result_original'],physical['native_root_slot'],
   operands,native_input['initial_operands_original'],original_cutoffs,env,
   root_slot['version'],root_slot['version9'],root_slot['flags'],root_slot['acl'],inputs)

  fields=('generation','native_input','generation_original','inputs','rows','root_slot',
   'physical','physical_original','physical_result','cutoffs','role','producer','producer_code',
   'containing_function','containing_code','errors')
  binding['original']=(binding,)+tuple(binding[name]for name in fields)
  require(generation['policy_transition']is None,'INPUT4_LOCAL_ONE_POLICY_CONTINUITY')
  actor=physical['actor'];holder=physical['holder']
  require(type(actor)is tuple and type(holder)is tuple
   and type(actor[0])is int and type(holder[0])is int and actor[0]>0 and holder[0]>0
   and actor[0]!=holder[0],'INPUT4_LOCAL_POLICY_ACTORS')
  policy_reads=[]
  label=(operands['stem']+'controller (enforce)\n').encode('ascii')
  for pid in (actor[0],holder[0]):
   path=_f.Path('/proc')/str(pid)/'attr'/'current'
   selected=tuple(r for r in physical['reads']if r['path']==path)
   require(len(selected)==1,'INPUT4_LOCAL_ONE_ACTUAL_POLICY_READ')
   r=selected[0];fd=r['fd_slot']
   require(r['owner']is owner and r['complete']is True and not r['errors']
    and type(r['raw'])is bytes and r['raw']==label
    and bytes(r['prefix'])==r['raw'] and r['last_returned']==b''
    and r['returned_bytes']==len(r['raw']) and type(fd)is dict
    and any(fd is slot for slot in physical['slots']) and fd['owner']is owner
    and fd['path']==path and fd['open_attempted']is True
    and fd['close_attempted']is True and fd['closed']is True and not fd['errors'],
    'INPUT4_LOCAL_COMPLETED_KERNEL_ENFORCED_POLICY_READ')
   policy_reads.append(r)
  transition=dict(generation=generation,generation_original=original,native_input=native_input,
   physical=physical,physical_original=binding['physical_original'],
   physical_result=binding['physical_result'],producer_original=po,
   actor_read=policy_reads[0],holder_read=policy_reads[1],label=label,
   cutoffs=original_cutoffs,errors=errors)
  transition['original']=(transition,generation,original,native_input,physical,
   physical['original'],physical['result_original'],po,policy_reads[0],policy_reads[1],
   label,original_cutoffs,errors)
  def original_startup_rejoin():
   startup=native_input['startup_source']
   require(startup['source_generation']is generation and startup['native_generation']is native_input['native_generation']
    and startup['startup_binding']is None and startup['roles']is None,
    'INITIAL_STARTUP_ONE_ORIGINAL_CONTINUITY_ISSUER')
   earlier=startup['pre_cold_result'];earlier_original=earlier['success_original']
   require(earlier is startup['pre_cold_attempt']and earlier['complete']is True
    and earlier_original[0]is earlier and earlier_original[1]is earlier['original']
    and earlier_original[2]is earlier['startup_attempt']
    and earlier_original[3]is earlier['product_original']
    and earlier_original[7]is native_input['origin_prebind_result_original']
    and earlier_original[8]is native_input['early_allocation_original']
    and earlier['native_input']is native_input and earlier['generation']is generation
    and earlier['source_original']is original and earlier['owner']is owner
    and earlier['errors']is errors and earlier['cutoffs'][0]==physical['origin_ns']
    and physical['operands']is native_input['initial_operands']
    and earlier['origin']['operands']is physical['operands'],
    'INITIAL_STARTUP_ORIGINAL_EARLY_PRODUCT_SAME_PHYSICAL_ADOPTION')
   attempt=earlier['startup_attempt'];startup['local_rejoin']=attempt
   require(attempt['metadata_complete']is True and attempt['complete']is False
    and 'physical_adoption'not in attempt,'INITIAL_STARTUP_ONE_PENDING_ACL_COMPLETION')
   attempt['binding']=binding;attempt['physical']=physical;attempt['producer_original']=po
   attempt['cutoffs']=original_cutoffs
   attempt['physical_adoption']=(attempt,earlier,earlier_original,binding,physical,
    physical['original'],physical['result_original'],po,original,original_cutoffs,errors)
   ci_original=earlier['ci_source_code_original']
   require(ci_original[0]is earlier and ci_original[1]is _f.sys.modules['tools.ci_branch_context']
    and ci_original[2]is ci_original[1].__dict__
    and ci_original[2]['_ORDINARY_INITIALIZED_MODULE_CODE_V1']is ci_original[3]
    and ci_original[6]is _facet_fn_initial_startup_prebind_v1
    and ci_original[6].__code__ is ci_original[7],'INITIAL_STARTUP_SAME_ORIGINAL_CI_SOURCE_CODE_ADOPTION')
   env=earlier['environment'];workspace,temp,run,attempt_name=(value for key,value in env)
   stem=operands['stem'];install=earlier['installation_root'];control=earlier['control_root_path']
   control_slot=opened(control,True)
   require(control_slot['version9']==earlier['control_root_version9'],
    'INITIAL_STARTUP_SAME_EARLIER_GENERATED_CONTROL_ROOT')
   # Native ACL observation remains with its original initialized owner.
   # No pre-cold metadata row was an accepted startup observation/census.
   for pending in earlier['pending_acl']:
    old=pending['original'];retained=pending['slot']
    expected=(pending,earlier,retained,pending['path'],pending['version'],pending['version9'],pending['flags'],owner,errors)
    require(type(old)is tuple and len(old)==len(expected)
     and all(left is right for left,right in zip(old,expected))and pending['complete']is False,
     'INITIAL_STARTUP_EXACT_UNCHANGED_PENDING_ACL_ORIGINAL')
    selected=None;failures=[]
    try:
     selected=opened(pending['path'],_f.stat.S_ISDIR(pending['version9'][2]))
     require(selected['version']==pending['version']and selected['version9']==pending['version9'],
      'INITIAL_STARTUP_SAME_IMMUTABLE_PENDING_ACL_GENERATION')
     selected['flags']=call('INITIAL_STARTUP_PENDING_ACL_FLAGS',native.flags,selected['returned_fd'])
     require(selected['flags']==pending['flags']and selected['flags']&16,
      'INITIAL_STARTUP_ORIGINAL_PENDING_ACL_FLAGS')
     acl(selected);rejoin(selected,directory=_f.stat.S_ISDIR(pending['version9'][2]),protected=True)
     pending['result']=(selected,selected['acl'],selected['acl_observation'],physical,original_cutoffs)
     pending['complete']=True
    except BaseException as error:failures.append(error)
    finally:
     if selected is not None and not selected['close_attempted']:
      try:close(selected)
      except BaseException as error:failures.append(error)
    _f._scan_raise_errors(failures)
   require(all(note['complete']is True for note in earlier['pending_acl']),
    'INITIAL_STARTUP_ALL_ORIGINAL_NATIVE_ACL_OBSERVATIONS_COMPLETE')
   for row in attempt['file_order']:
    info=call('INITIAL_STARTUP_ORIGINAL_FILE_FINAL_GENERATION',_f.os.lstat,row['path'])
    require(v9(info)==row['source']['version9'],
     'INITIAL_STARTUP_ORIGINAL_IMMUTABLE_C_FILE_GENERATION')
    row['expected']=(str(row['baseline']['path']),row['baseline']['version9'],row['baseline']['flags'],row)
    row['causal_c_original']=earlier['product_original'];row['complete']=True
   for row in attempt['directories'].values():
    require(row['metadata_complete']is True and (row['duplicate']is not None
     or row['roster_complete']is True),'INITIAL_STARTUP_COMPLETE_ORIGINAL_DIRECTORY_METADATA')
    info=call('INITIAL_STARTUP_ORIGINAL_DIRECTORY_FINAL_GENERATION',_f.os.lstat,row['path'])
    require(v9(info)==row['source']['version9'],'INITIAL_STARTUP_SAME_ORIGINAL_DIRECTORY_GENERATION')
    row['complete']=True
   def canonical(value):
    selected=str(path(value))
    for hop in range(40):
     changed=False
     for observed,target,version in attempt['aliases']:
      if selected==observed or selected.startswith(observed+'/'):
       require(v9(call('INITIAL_STARTUP_ALIAS_CURRENT',_f.os.lstat,observed))==version
        and call('INITIAL_STARTUP_ALIAS_TARGET_CURRENT',_f.os.readlink,observed)==target,
        'INITIAL_STARTUP_ORIGINAL_ALIAS_STILL_HELD')
       base=target if target.startswith('/')else str(_f.Path(observed).parent)+'/'+target
       selected=_f.os.path.normpath(base)+selected[len(observed):];path(selected)
       require(_f.Path(selected).is_relative_to(install),'INITIAL_STARTUP_ALIAS_INSIDE_ORIGINAL_INSTALLATION')
       changed=True;break
     if not changed:return selected
    raise ValueError('INITIAL_STARTUP_ALIAS_CHAIN_DOMAIN')
   def read_chunk(slot,request,label):
    quantum=_f._ordinary_initial_native_quantum_v1(native_input,request)
    require(quantum==request,'INITIAL_STARTUP_EXACT_REQUEST_PROSPECTIVE_ADMISSION')
    _f._ordinary_initial_native_debit_v1(native_input,label)
    raw=_f.os.read(slot['returned_fd'],request)
    delivered(raw,request,'INITIAL_STARTUP_RETURNED_BYTES');return raw
   # The original live interpreter and every already loaded JSON module are
   # identified from actual module/spec objects. Builtins have no fake file.
   runner=generation['runner'];sys=runner.sys;c=native.ctypes
   modules=tuple((name,sys.modules.get(name))for name in ('json','json.decoder','json.scanner','_json','_sre'))
   require(all(type(module)is type(sys)for name,module in modules),
    'INITIAL_STARTUP_ACTUAL_ALREADY_LOADED_JSON_CLOSURE')
   bootstrap=sys.modules['_frozen_importlib'];spec_class=bootstrap.__dict__['ModuleSpec']
   require(type(spec_class)is type and spec_class.__module__=='_frozen_importlib',
    'INITIAL_STARTUP_PINNED_MODULESPEC_CLASS')
   actual=dict(modules);api=c.pythonapi;api_class=api._FuncPtr
   require(type(api)is c.PyDLL and api._name is None and api_class._flags_==c._FUNCFLAG_CDECL|c._FUNCFLAG_PYTHONAPI,
    'INITIAL_STARTUP_CURRENT_SAME_LOADED_PYTHONAPI')
   version_fn=call('INITIAL_STARTUP_API_GETVERSION',api.__getitem__,'Py_GetVersion')
   getter=call('INITIAL_STARTUP_API_GETFUNCTION',api.__getitem__,'PyCFunction_GetFunction')
   require(type(version_fn)is type(getter)is api_class,'INITIAL_STARTUP_ORIGINAL_API_POINTER_TYPES')
   getter.argtypes=(c.py_object,);getter.restype=c.c_void_p
   version_address=call('INITIAL_STARTUP_API_CAST',c.cast,version_fn,c.c_void_p).value
   pointers=[('libpython',version_address,version_fn)]
   for role,value in (('_json',actual['_json'].__dict__['scanstring']),('_sre',actual['_sre'].__dict__['compile'])):
    require(type(value)is type(len),'INITIAL_STARTUP_ACTUAL_BUILTIN_FUNCTION_OBJECT')
    address=call('INITIAL_STARTUP_API_FUNCTION_ADDRESS',getter,value)
    pointers.append((role,address,value))
   require(all(type(address)is int and 0<address<1<<64 for role,address,value in pointers),
    'INITIAL_STARTUP_ACTUAL_NATIVE_POINTER_VALUES')
   attempt['symbols']=pointers
   maps=opened('/proc/'+str(owner[0])+'/maps');map_errors=[]
   try:
    # Procfs extent is zero: acquire through its original bounded incremental
    # text semantics, not fstat.size or the ordinary physical-file EOF owner.
    chunks=bytearray()
    while True:
     raw=read_chunk(maps,min(65536,1048577-len(chunks)),'INITIAL_STARTUP_MAPS_READ')
     if not raw:break
     chunks.extend(raw);require(len(chunks)<=1048576,'INITIAL_STARTUP_ORIGINAL_MAPS_LIMIT')
    raw=bytes(chunks);require(raw.endswith(b'\n'),'INITIAL_STARTUP_COMPLETE_MAPS_LINES')
    from tools.validation_scope_registry import _ordinary_runtime7_map_line_registry_v1 as map_line
    entries=tuple(map_line(line)for line in raw.splitlines());attempt['maps'].append((maps,raw,entries))
   except BaseException as error:map_errors.append(error)
   finally:dispose(maps,map_errors)
   _f._scan_raise_errors(map_errors)
   executable=canonical(sys.executable)
   require(executable in attempt['files'],'INITIAL_STARTUP_EXECUTABLE_IN_ORIGINAL_C_INVENTORY')
   exe_row=attempt['files'][executable]
   exe=call('INITIAL_STARTUP_ACTUAL_EXE',_f.os.stat,'/proc/'+str(owner[0])+'/exe')
   require(v9(exe)==exe_row['source']['version9'],'INITIAL_STARTUP_ACTUAL_EXECUTED_ORIGINAL_FILE')
   def pointer_row(address):
    matches=tuple(row for row in entries if row[0]<=address<row[1]and row[2][2:3]==b'x')
    require(len(matches)==1 and matches[0][6]>0,'INITIAL_STARTUP_EXACT_NATIVE_MAPPING')
    item=matches[0]
    hits=tuple(row for row in attempt['file_order']if
     (_f.os.major(row['version'][0]),_f.os.minor(row['version'][0]),row['version'][1])==item[4:7])
    require(len(hits)==1,'INITIAL_STARTUP_NATIVE_MAPPING_IN_ORIGINAL_C_FILES')
    return hits[0],item
   native_rows=tuple((role,*pointer_row(address),address,value)for role,address,value in pointers)
   lib_row=native_rows[0][1];roles=[('executable','EXECUTABLE',exe_row),
    ('libpython','STATIC_IN_EXECUTABLE'if lib_row is exe_row else'MAPPED_LIBRARY',lib_row)]
   for role,name in (('_json','_json'),('_sre','_sre'),('json.__init__','json'),('json.decoder','json.decoder'),('json.scanner','json.scanner')):
    module=actual[name];spec=module.__dict__.get('__spec__')
    require(type(spec)is spec_class and type(spec.__dict__)is dict,'INITIAL_STARTUP_ACTUAL_SPEC_OBJECT')
    values=spec.__dict__;origin=values.get('origin');loader=values.get('loader')
    require(values.get('name')==name and type(origin)is str,'INITIAL_STARTUP_ACTUAL_SPEC_ORIGIN')
    if origin=='built-in':
     require(role in ('_json','_sre')and name in sys.builtin_module_names
      and loader is bootstrap.__dict__['BuiltinImporter'],'INITIAL_STARTUP_SUPPORTED_BUILTIN_ROLE')
     row=next(r[1]for r in native_rows if r[0]==role)
     require(row is exe_row or row is lib_row,'INITIAL_STARTUP_BUILTIN_ACTUAL_PYTHON_BACKING');mode='BUILTIN'
    else:
     require(origin!='frozen'and _f.Path(origin).is_absolute(),'INITIAL_STARTUP_SUPPORTED_FILE_ORIGIN')
     key=canonical(origin);require(key in attempt['files'],'INITIAL_STARTUP_MODULE_ORIGINAL_C_FILE')
     row=attempt['files'][key]
     require(v9(call('INITIAL_STARTUP_MODULE_FILE',_f.os.stat,origin))==row['source']['version9'],
      'INITIAL_STARTUP_SAME_ACTUAL_MODULE_FILE')
     if role in ('_json','_sre'):
      require(row is next(r[1]for r in native_rows if r[0]==role),'INITIAL_STARTUP_EXTENSION_FILE_AND_C_BACKING');mode='EXTENSION_FILE'
     else:require(_f.Path(origin).suffix=='.py','INITIAL_STARTUP_ORIGINAL_PYTHON_SOURCE');mode='PYTHON_SOURCE'
    snapshot=(module,spec,origin,loader,module.__dict__.get('__file__'),module.__dict__.get('__cached__'))
    attempt['module_observations'].append((role,name,snapshot));roles.append((role,mode,row))
   # These standard-library facets are acquired only after ALL original
   # installation files have matched their independent earlier C baselines.
   import sysconfig,site,struct
   version=tuple(sys.version_info[:3]);abi=(sys.implementation.cache_tag,sysconfig.get_config_var('SOABI'),
    struct.calcsize('P')*8,sysconfig.get_config_var('Py_GIL_DISABLED'),getattr(sys,'abiflags',''))
   require(sys.implementation.name=='cpython'and sys.platform=='linux'
    and version==(3,14,6)and abi[2:4]==(64,0),'INITIAL_STARTUP_SUPPORTED_CURRENT_ABI')
   stdlib=tuple(dict.fromkeys(str(_f.Path(sysconfig.get_path(k)).absolute())for k in ('stdlib','platstdlib')))
   sites=tuple(str(_f.Path(p).absolute())for p in site.getsitepackages())
   executable_path=_f.Path(sys.executable).absolute()
   configs=tuple(dict.fromkeys((str(executable_path.parent/'pyvenv.cfg'),str(executable_path.parent.parent/'pyvenv.cfg'),
    str(executable_path.with_suffix('._pth')),str(executable_path.parent/('python'+str(version[0])+str(version[1])+'._pth')))))
   search=tuple(dict.fromkeys((workspace,str(_f.Path(workspace)/'tools'),str(executable_path.parent),*stdlib,*sites)))
   customizers=tuple(str(_f.Path(root)/(name+suffix))for root in search for name in ('sitecustomize','usercustomize')
    for suffix in ('.py','.pyc','.pyd','.so',''))
   def status(value):
    selected=_f.Path(value);parent=str(selected.parent)
    if parent not in attempt['directories']:
     ancestor=selected.parent
     while str(ancestor)not in attempt['directories']and ancestor!=ancestor.parent:ancestor=ancestor.parent
     require(str(ancestor)in attempt['directories'],'INITIAL_STARTUP_COMPLETE_APPLICABLE_PARENT')
     component=selected.relative_to(ancestor).parts[0]
     require(_f.os.fsencode(component)not in attempt['directories'][str(ancestor)]['names'],
      'INITIAL_STARTUP_ORIGINAL_ABSENT_ANCESTOR')
     attempt['absences'].append(value);return None
    row=attempt['directories'][parent]
    match=tuple(member for member in row['members']if member[0]==_f.os.fsencode(selected.name))
    if not match:attempt['absences'].append(value);return None
    require(len(match)==1,'INITIAL_STARTUP_EXACT_ORIGINAL_STATUS');return match[0][2]
   for value in configs:
    kind=status(value)
    require(kind is None or kind==_f.stat.S_IFREG and not value.endswith('._pth'),
     'INITIAL_STARTUP_SUPPORTED_ORIGINAL_CONFIG')
   for value in customizers:require(status(value)is None,'INITIAL_STARTUP_NO_UNADMITTED_ORIGINAL_CUSTOMIZER')
   loader_environment={key:value for key,value in _f.os.environ.items()if key.upper()in
    ('PATH','SYSTEMROOT','WINDIR','LD_LIBRARY_PATH','LD_PRELOAD','DYLD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES','__PYVENV_LAUNCHER__')}
   require(not any(key.upper()in ('LD_PRELOAD','DYLD_INSERT_LIBRARIES','__PYVENV_LAUNCHER__')for key in loader_environment),
    'INITIAL_STARTUP_NO_UNADMITTED_LOADER_INJECTION')
   for role,name,snapshot in attempt['module_observations']:
    module,spec,origin,loader,file,cached=snapshot
    require(sys.modules[name]is module and module.__dict__.get('__spec__')is spec
     and spec.__dict__.get('origin')==origin and spec.__dict__.get('loader')is loader
     and module.__dict__.get('__file__')==file and module.__dict__.get('__cached__')==cached,
     'INITIAL_STARTUP_SAME_LOADED_MODULE_CONTINUITY')
   physical_live();rejoin(control_slot,directory=True)
   basis=dict(files=attempt['files'],directories={key:tuple((_f.os.fsdecode(name),
    'directory'if kind==_f.stat.S_IFDIR else'file'if kind==_f.stat.S_IFREG else'alias')
    for name,version,kind in row['members'])for key,row in attempt['directories'].items()},absent=tuple(attempt['absences']))
   binding9=dict(observation=attempt,version=version,abi=abi,stdlib_roots=stdlib,site_roots=sites,
    loader_environment=loader_environment,config_paths=configs,customizer_paths=customizers,startup_basis=basis)
   roles=tuple(roles)
   require(set(binding9)==set(startup['expected_startup_keys'])and set(basis)==set(startup['expected_basis_keys'])
    and tuple(row[0]for row in roles)==startup['expected_roles']and not errors,
    'INITIAL_STARTUP_COMPLETE_ORIGINAL_C_CONTINUITY_RESULT')
   attempt.update(binding9=binding9,roles=roles,complete=True)
   attempt['success_original']=(attempt,attempt['original'],binding9,basis,roles,attempt['pairs'],
    attempt['module_observations'],attempt['maps'],attempt['symbols'],control_slot,errors)
   startup['startup_binding']=binding9;startup['roles']=roles
  original_startup_rejoin()
  a['result']=binding;a['complete']=True;binding['complete']=True;root_slot['complete']=True
  generation['protected_inputs']=inputs;generation['native_input_binding']=binding
  generation['policy_transition']=transition
  generation['keeper_borrow_original']=binding['original']
  generation['control_source_originals']=[records[i]for i in (2,1,3,5)]
  return binding
 except BaseException as error:
  if all(error is not old for old in errors):errors.append(error)
  a['error']=error
  # SAME physical slots/reads and every failed admission/prefix remain retained.
  # The local issuer never changes mode/owner/flags or restores outside history.
  raise


def _facet_fn_control_python_ast_request_v1(layout, profile):
    import tools.validation_reliability as _f
    # Independently source-selected AST conversion profile: non-singleton
    # node field-count histogram, exact list objects/slots, and the four
    # native position attributes actually converted through PyLong_FromLong.
    # Original Source/flags/profile association must be bound before parsing.
    if type(profile) is not tuple or len(profile) != 5:
        raise ValueError('CONTROL_ORIGINAL_AST_CONVERSION_PROFILE')
    fields, lists, slots, positions, position_bits = profile
    if (type(fields) is not tuple or any(type(v) is not int or v < 0
            for v in (lists, slots, positions, position_bits))
            or _f._ordinary_data_size_v1(layout, 'pointer') != 8):
        raise ValueError('CONTROL_ORIGINAL_AST_CONVERSION_LAYOUT')
    nodes, dictionaries, active_old_table = 0, 0, 0
    for count_fields, occurrences in fields:
        if (type(count_fields) is not int or count_fields < 0
                or type(occurrences) is not int or occurrences < 0):
            raise ValueError('CONTROL_ORIGINAL_AST_FIELD_COUNTS')
        nodes += occurrences
        if count_fields == 0:
            continue
        # Original stock Unicode-key dictionary, no deletion or arbitrary
        # setters. Growth uses occupied*3 and a power-of-two table. The final
        # table stays on its node; one active resize can overlap its old table.
        capacity, occupied, old = 8, 0, 0
        for _ in range(count_fields):
            if occupied >= 2 * capacity // 3:
                old = capacity
                capacity = 8
                while capacity < 3 * occupied:
                    capacity *= 2
            occupied += 1
        width = 1 if capacity < 256 else 2 if capacity < 65536 else 4
        table = 32 + capacity * width + (2 * capacity // 3) * 16
        dictionaries += occurrences * (64 + table)
        if old:
            old_width = 1 if old < 256 else 2 if old < 65536 else 4
            active_old_table = max(active_old_table,
                32 + old * old_width + (2 * old // 3) * 16)
    integer = (_f._ordinary_data_size_v1(layout, 'int_prefix')
        + _f._ordinary_data_size_v1(layout, 'int_digit_bytes')
        * ((max(1, position_bits) + _f._ordinary_data_size_v1(layout, 'int_digit_bits') - 1)
            // _f._ordinary_data_size_v1(layout, 'int_digit_bits')))
    # Python-ast.c ast2obj_list uses PyList_New(n), with exactly n pointers;
    # this is not append/geometric list growth. Identifier/constant/string
    # fields use Py_NewRef and do not copy their complete source per field.
    return (
        ('PYTHON_AST_NON_SINGLETON_OBJECTS_AND_FINAL_DICTS',
            nodes * (24 + _f._ordinary_data_size_v1(layout, 'gc')) + dictionaries),
        ('PYTHON_AST_EXACT_LISTS_AND_SLOTS',
            lists * _f._ordinary_data_size_v1(layout, 'list_prefix') + 8 * slots),
        ('PYTHON_AST_POSITION_INTEGER_CONVERSIONS', positions * integer),
        ('PYTHON_AST_ONE_ACTIVE_DICTIONARY_RESIZE', active_old_table),
    )


def _facet_fn_initial_native_debit_v1(native_input, operation, *, raw=None,
  request_bytes=None, settling=False):
 """Continue the original Source prefix before and after physical acquisition."""
 import tools.validation_reliability as _f
 _f._preflight_require_v1(type(native_input) is dict
  and native_input['owner'] == (_f.os.getpid(), _f.threading.get_ident())
  and type(operation) is str and operation,
  'ORDINARY_INITIAL_NATIVE_DEBIT_OWNER')
 record = _f._ordinary_initial_prefix_v1(native_input)
 profile = native_input['early_profile']
 _f._preflight_require_v1(type(profile) is tuple and len(profile) == 12
  and profile is record['profile'] and profile[0] is native_input
  and profile[6] is None
  and record['native_input'] is native_input and record['errors'] is native_input['errors']
  and type(profile[8]) is int and profile[8] > 0
  and type(profile[9]) is int and profile[9] > 0
  and type(record['prefix_original']) is tuple and len(record['prefix_original']) == 8
  and record['prefix_original'][0] is record
  and record['prefix_original'][6] is record['operations'],
  'ORDINARY_INITIAL_SAME_ORIGINAL_EARLY_DEBIT_RECORD')
 allocation = native_input['early_allocation_original']
 _f._preflight_require_v1(type(allocation) is tuple and len(allocation) == 4
  and allocation[0] is native_input and allocation[1] is profile
  and type(allocation[2]) is dict and type(allocation[3]) is dict
  and set(allocation[2]) == set(allocation[3])
   == {'work_calls', 'work_bytes', 'settlement_calls', 'settlement_bytes', 'work_loops', 'settlement_loops'}
  and all(type(value) is int and value > 0 for value in allocation[2].values())
  and all(type(value) is int and value >= 0 for value in allocation[3].values())
  and profile[8] == allocation[2]['work_calls'] + allocation[2]['settlement_calls']
  and profile[9] == allocation[2]['work_bytes'] + allocation[2]['settlement_bytes'],
  'ORDINARY_INITIAL_SOURCE_ISSUED_DISJOINT_WORK_AND_SETTLEMENT_ALLOCATION')
 _ordinary_ci_initial_common_source_check_v1(native_input,profile,allocation)
 pool = ('settlement' if settling else 'work') + ('_calls' if raw is None else '_bytes')
 allocation[3][pool] += 1 if raw is None else len(raw)
 if raw is None:
  record['operation_calls'] += 1
  record['operations'].append(operation)
  _f._preflight_require_v1(allocation[3][pool] <= allocation[2][pool]
   and record['operation_calls'] <= profile[8],
   'ORDINARY_INITIAL_PROSPECTIVE_NATIVE_CALL_ALLOCATION')
 else:
  _f._preflight_require_v1(type(raw) is bytes and type(request_bytes) is int
   and 0 < request_bytes <= 65536,
   'ORDINARY_INITIAL_ORIGINAL_RETURNED_NATIVE_OPERAND')
  record['last_supervised_returned'] = raw
  record['returned_bytes'] += len(raw)
  _f._preflight_require_v1(len(raw) <= request_bytes
   and allocation[3][pool] <= allocation[2][pool] and record['returned_bytes'] <= profile[9],
   'ORDINARY_INITIAL_PROSPECTIVE_NATIVE_RETURNED_ALLOCATION')
 prebind=native_input.get('origin_prebind')
 if type(prebind)is dict and prebind.get('complete')is False and operation.startswith('ORIGIN_PREBIND_'):
  labels=tuple('ORIGIN_PREBIND_'+name for name in ('OWNER','PATH_METADATA','COMPONENT_OPEN',
   'HANDLE_METADATA','INHERITANCE','PATH_REJOIN','READ','CWD','PIDFD_OPEN','PIDFD_OBSERVE',
   'NAMESPACE','ONE_CLOSE','RETURNED_BYTES'))
  fields=('native_input','source_return','preloader_source_anchor','preloader_programme_original',
   'initial_source_request','prefix_original','owner','errors','producer','producer_code',
   'containing_function','containing_code','operations','slots','reads')
  old=prebind.get('original');producer=prebind.get('producer');container=prebind.get('containing_function')
  namespace=native_input['source_generation']['module_namespace']
  _f._preflight_require_v1(_f.sys.platform=='linux' and operation in labels
   and prebind.get('active_operation')==operation and type(settling)is bool
   and (operation=='ORIGIN_PREBIND_ONE_CLOSE')is settling
   and (raw is not None)==(operation=='ORIGIN_PREBIND_RETURNED_BYTES')
   and type(old)is tuple and len(old)==16 and old[0]is prebind
   and all(old[i+1]is prebind[name] for i,name in enumerate(fields))
   and prebind['native_input']is native_input and prebind['owner']is record['owner']
   and prebind['errors']is record['errors'] and prebind['operations']is record['operations']
   and prebind['source_return']is native_input['preloader_source_return']
   and prebind['preloader_source_anchor']is native_input['preloader_source_anchor']
   and prebind['preloader_programme_original']is native_input['preloader_programme_original']
   and prebind['initial_source_request']is profile and prebind['prefix_original']is record['prefix_original']
   and type(prebind['slots'])is list and type(prebind['reads'])is list
   and type(producer)is type(_f._ordinary_initial_native_object_v1)
   and producer.__globals__ is namespace is _f.__dict__
   and producer.__name__=='_original_prebind_v1' and producer.__code__ is prebind['producer_code']
   and container is _f._ordinary_initial_native_object_v1
   and container.__globals__ is namespace and container.__code__ is prebind['containing_code']
   and any(code is producer.__code__ for code in container.__code__.co_consts)
   and any(code is native_input['preloader_source_anchor'][14] for code in container.__code__.co_consts),
   'ORDINARY_INITIAL_EXACT_ORIGIN_ONLY_PREBIND_SOURCE_LOAN')
  frame=_f.sys._getframe(2);original_frame=frame
  try:
   loan=prebind.get('keeper_observation_loans');facet=_facet_fn_initial_keeper_observation_loans_v1
   if type(loan)is dict and loan.get('complete')is False and loan.get('active_operation')==operation:
    fields=('native_input','prebind','prebind_original','source_anchor','holder','root','owner','errors',
     'producer','producer_code','module_namespace','initializer_code','slots','observations','roles')
    original=loan['original'];initial=globals()['_ORDINARY_INITIALIZED_MODULE_CODE_V1']
    _f._preflight_require_v1(type(original)is tuple and len(original)==16 and original[0]is loan
     and all(original[i+1]is loan[name]for i,name in enumerate(fields))
     and loan['native_input']is native_input and loan['prebind']is prebind
     and loan['prebind_original']is old and loan['source_anchor']is native_input['preloader_source_anchor']
     and loan['owner']is record['owner']and loan['errors']is record['errors']
     and loan['producer']is facet and loan['producer_code']is facet.__code__
     and facet.__globals__ is globals()is loan['module_namespace']
     and loan['initializer_code']is initial and any(code is facet.__code__ for code in initial.co_consts)
     and frame.f_globals is globals()and any(code is frame.f_code for code in facet.__code__.co_consts),
     'ORDINARY_INITIAL_EXACT_KEEPER_LOAN_PRIVATE_FACET_SOURCE')
    facet_frame=frame.f_back
    _f._preflight_require_v1(facet_frame is not None and facet_frame.f_code is facet.__code__
     and facet_frame.f_locals.get('record')is prebind and facet_frame.f_locals.get('native_input')is native_input,
     'ORDINARY_INITIAL_ACTIVE_PRIVATE_KEEPER_LOAN_FRAME')
    original_frame=facet_frame.f_back
   elif frame.f_code is not producer.__code__:
    _f._preflight_require_v1(frame.f_globals is namespace
     and any(code is frame.f_code for code in producer.__code__.co_consts),
     'ORDINARY_INITIAL_ORIGIN_ONLY_ORIGINAL_NESTED_HELPER')
    original_frame=frame.f_back
   _f._preflight_require_v1(original_frame is not None
    and original_frame.f_code is producer.__code__ and original_frame.f_globals is namespace
    and original_frame.f_locals.get('record')is prebind
    and original_frame.f_locals.get('native_input')is native_input,
    'ORDINARY_INITIAL_ACTIVE_ORIGINAL_PREBIND_FRAME')
  finally:
   del frame,original_frame
  # Only this fixed origin tranche borrows the original outside keeper wall.
  # It issues no timestamp; generic/object/constructor work keeps the cutoff law.
  return
 request = native_input['original_origin_request']
 origin = native_input['original_origin_ns']
 execution = native_input['original_execution_cutoff_ns']
 settlement = native_input['original_settlement_cutoff_ns']
 _f._preflight_require_v1(profile[6] is None
  and type(request) is dict and profile[5] is request
  and request['source_generation'] is profile[1]
  and type(origin) is int and origin > 0
  and type(execution) is int and execution == origin + 3600 * 10**9
  and type(settlement) is int and settlement == origin + 3720 * 10**9
  and request['origin_ns'] == origin and request['deadline_ns'] == settlement,
  'ORDINARY_INITIAL_UNCHANGED_PENDING_PROFILE_AND_GENUINE_SEPARATE_CUTOFFS')
 cutoff = settlement if settling else execution
 _f._preflight_require_v1(type(cutoff) is int and cutoff > 0
  and cutoff <= settlement and _f.time.monotonic_ns() < cutoff,
  'ORDINARY_INITIAL_ORIGINAL_WORK_OR_SETTLEMENT_CUTOFF')


def _facet_fn_initial_preloader_return_check_v1(native_input):
 """Join the SAME pending Source return; this issues no physical authority."""
 import tools.validation_reliability as _f
 _f._preflight_require_v1(type(native_input) is dict,
  'ORDINARY_INITIAL_PRELOADER_RETURN_INPUT')
 attempt = native_input.get('entry_attempt')
 anchor = native_input.get('preloader_source_anchor')
 _f._preflight_require_v1(type(attempt) is dict
  and type(anchor) is tuple and len(anchor) == 16
  and attempt.get('native_input') is native_input
  and attempt.get('initial_source_anchor') is anchor,
  'ORDINARY_INITIAL_PRELOADER_RETURN_ORIGINAL_ENTRY_ANCHOR')
 row, original, input_original, returned, programme = (
  anchor[0], anchor[2], anchor[3], anchor[4], anchor[5])
 source_original, native_original, startup_original, origin_original = anchor[6:10]
 emitter_original, origin_join, request_original = anchor[10:13]
 _f._preflight_require_v1(anchor[1] is native_input
  and type(row) is dict and native_input.get('preloader_source_attempt') is row
  and row.get('return_original') is anchor
  and type(original) is tuple and len(original) == 9
  and type(input_original) is tuple and len(input_original) == 6
  and type(returned) is tuple and len(returned) == 8
  and type(programme) is tuple and len(programme) == 23
  and type(source_original) is tuple and len(source_original) == 17
  and type(native_original) is tuple and len(native_original) == 10
  and type(startup_original) is tuple and len(startup_original) == 12
  and type(origin_original) is tuple and len(origin_original) == 15
  and type(emitter_original) is tuple and len(emitter_original) == 7
  and type(origin_join) is tuple and len(origin_join) == 11
  and type(request_original) is tuple and len(request_original) == 5,
  'ORDINARY_INITIAL_PRELOADER_RETURN_ORIGINAL_SHAPES')
 errors = anchor[15]
 owner = original[1]
 runner, namespace, initializer, entry, entry_code = original[4:9]
 source, generation, startup, request = returned[1:5]
 origin = origin_original[0]
 module, module_namespace, native_class, constructor, constructor_code = programme[11:16]
 method, method_code, code_paths, workflow = programme[16:20]
 emitter, emitter_code = emitter_original[1:3]
 origin_decoder, origin_code, receipt, receipt_code, properties = origin_original[8:13]
 _f._preflight_require_v1(type(errors) is list and not errors
  and attempt.get('errors') is errors and native_input.get('errors') is errors
  and attempt.get('original') is original
  and original[0] is attempt and original[2] is errors
  and original[3] is attempt.get('phase')
  and native_input.get('entry_original') is original
  and native_input.get('owner') is owner and attempt.get('owner') is owner
  and owner == (_f.os.getpid(), _f.threading.get_ident())
  and native_input.get('original') is input_original
  and all(left is right for left, right in zip(input_original,
   (native_input, attempt, original, owner, errors,
    native_input.get('initialized_storage_attempts'))))
  and runner.__dict__ is namespace
  and namespace.get('_ORDINARY_BOOTSTRAP_ENTRY_ATTEMPT_V1') is attempt
  and namespace.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1') is initializer
  and namespace.get('_ordinary_linux_provision_v1') is entry
  and entry.__globals__ is namespace and entry.__code__ is entry_code,
  'ORDINARY_INITIAL_PRELOADER_RETURN_IDENTICAL_ENTRY_INPUT_AND_ERRORS')
 _f._preflight_require_v1(native_input.get('preloader_source_return') is returned
  and attempt.get('initial_source_return') is returned
  and row.get('result') is returned
  and all(left is right for left, right in zip(returned,
   (native_input, source, generation, startup, request, row,
    programme, request_original)))
  and row.get('programme_original') is programme
  and native_input.get('preloader_programme_original') is programme
  and row.get('native_input') is native_input
  and row.get('entry_original') is original
  and row.get('owner') is owner and row.get('errors') is errors
  and row.get('producer') is anchor[13]
  and row.get('producer_code') is anchor[14]
  and anchor[13].__code__ is anchor[14]
  and all(left is right for left, right in zip(programme,
   (row, native_input, original, source, generation, startup,
    runner, namespace, initializer, entry, entry_code,
    module, module_namespace, native_class, constructor,
    constructor_code, method, method_code, code_paths, workflow,
    anchor[13], anchor[14], errors))),
  'ORDINARY_INITIAL_PRELOADER_RETURN_IDENTICAL_PUBLICATION_AND_PROGRAMME')
 _f._preflight_require_v1(type(source) is dict and type(generation) is dict
  and type(startup) is dict and type(origin) is dict
  and native_input.get('source_generation') is source
  and native_input.get('native_generation') is generation
  and native_input.get('startup_source') is startup
  and row.get('source_generation') is source
  and row.get('native_generation') is generation
  and row.get('startup') is startup
  and source.get('original') is source_original
  and all(left is right for left, right in zip(source_original,
   (source, native_input, original, runner, namespace, initializer,
    entry, entry_code, module, module_namespace, method, method_code,
    code_paths, workflow, source_original[14],
    source.get('physical_observations'), errors)))
  and all(source.get(key) is value for key, value in (
   ('native_input', native_input), ('entry_original', original),
   ('runner', runner), ('namespace', namespace), ('initializer', initializer),
   ('entry', entry), ('entry_code', entry_code), ('module', module),
   ('module_namespace', module_namespace), ('native_method', method),
   ('native_method_code', method_code), ('code_paths', code_paths),
   ('workflow', workflow),
   ('expected_module_closure', source_original[14]), ('errors', errors)))
  and generation.get('original') is native_original
  and all(left is right for left, right in zip(native_original,
   (generation, native_input, source, native_class, constructor,
    constructor_code, method, method_code,
    generation.get('physical_observations'), errors)))
  and all(generation.get(key) is value for key, value in (
   ('native_input', native_input), ('source_generation', source),
   ('native_class', native_class), ('constructor', constructor),
   ('constructor_code', constructor_code), ('native_method', method),
   ('native_method_code', method_code), ('errors', errors)))
  and startup.get('original') is startup_original
  and all(left is right for left, right in zip(startup_original,
   (startup, native_input, source, generation, original[3], code_paths,
    workflow, startup.get('expected_startup_keys'),
    startup.get('expected_basis_keys'), startup.get('expected_roles'),
    startup.get('physical_observations'), errors)))
  and all(startup.get(key) is value for key, value in (
   ('native_input', native_input), ('source_generation', source),
   ('native_generation', generation), ('phase', original[3]),
   ('code_paths', code_paths), ('workflow', workflow), ('errors', errors))),
  'ORDINARY_INITIAL_PRELOADER_RETURN_IDENTICAL_PENDING_CARRIERS')
 _f._preflight_require_v1(row.get('emitter_original') is emitter_original
  and row.get('emitter') is emitter
  and all(left is right for left, right in zip(emitter_original,
   (row, emitter, emitter_code, runner, namespace, initializer, programme)))
  and namespace.get('_ordinary_bootstrap_initial_source_request_v1') is emitter
  and emitter.__globals__ is namespace and emitter.__code__ is emitter_code
  and type(request) is tuple and len(request) == 12
  and row.get('source_request') is request
  and native_input.get('initial_source_request') is request
  and all(request[index] is value for index, value in (
   (0, native_input), (1, source), (2, generation), (3, startup),
   (4, original[3]), (5, origin), (6, None),
   (10, emitter), (11, emitter_code)))
  and row.get('origin_request') is origin
  and native_input.get('original_origin_request') is origin
  and origin.get('original') is origin_original
  and all(left is right for left, right in zip(origin_original,
   (origin, native_input, source, generation, startup, original[3],
    method, method_code, origin_decoder, origin_code, receipt,
    receipt_code, properties, programme, errors)))
  and all(origin.get(key) is value for key, value in (
   ('native_input', native_input), ('source_generation', source),
   ('native_generation', generation), ('startup', startup),
   ('phase', original[3]), ('selection', method),
   ('selection_code', method_code), ('producer', origin_decoder),
   ('producer_code', origin_code), ('receipt_producer', receipt),
   ('receipt_code', receipt_code), ('properties', properties), ('errors', errors)))
  and origin_decoder.__code__ is origin_code
  and receipt.__code__ is receipt_code
  and row.get('origin_request_original') is origin_join
  and all(left is right for left, right in zip(origin_join,
   (row, request, origin, programme, emitter, emitter_code,
    native_input, source, generation, startup, original[3])))
  and row.get('source_request_original') is request_original
  and all(left is right for left, right in zip(request_original,
   (row, request, programme, emitter_original, origin_join))),
  'ORDINARY_INITIAL_PRELOADER_RETURN_IDENTICAL_SOURCE_AND_ORIGIN_REQUEST')
 _f._preflight_require_v1(module.__dict__ is module_namespace
  and _f.sys.modules.get(native_class.__module__) is module
  and module_namespace.get('_LinuxSourceNativeV2') is native_class
  and native_class is _f._LinuxSourceNativeV2
  and native_class.__dict__.get('__init__') is constructor
  and constructor.__globals__ is module_namespace
  and constructor.__code__ is constructor_code
  and type(native_class.__dict__.get(
   '_ordinary_initial_native_product_v1')) is classmethod
  and native_class.__dict__[
   '_ordinary_initial_native_product_v1'].__func__ is method
  and method.__globals__ is module_namespace and method.__code__ is method_code
  and module_namespace.get('_ordinary_initial_manager_origin_v1') is origin_decoder
  and module_namespace.get('_ordinary_initial_manager_receipt_v1') is receipt,
  'ORDINARY_INITIAL_PRELOADER_RETURN_SAME_FIXED_PRODUCERS')
 return returned


def _facet_fn_runtime7_bootstrap_staged_request_v1(layout, installation):
 import tools.validation_reliability as _f
 producer = _f._ordinary_runtime7_bootstrap_staged_request_v1
 if type(installation) is not dict:
  raise ValueError('BOOTSTRAP_STAGED_ORIGINAL_INSTALLATION')
 original = installation.get('original')
 profile = installation.get('bootstrap_request_profile_original')
 if (type(original) is not tuple or len(original) != 17
   or original[0] is not installation
   or original[1] is not installation.get('scope')
   or original[2] is not installation.get('install')
   or original[7] is not installation.get('rows')
   or original[9] is not installation.get('files')
   or type(profile) is not tuple or len(profile) != 7
   or profile[0] is not installation or profile[1] is not original[1]
   or profile[2] is not original[2]
   or profile[6] is not producer
   or installation.get('complete') is not True or installation.get('errors')):
  raise ValueError('BOOTSTRAP_STAGED_SOURCE_PROFILE_OWNER')
 row, expected, reviewed = profile[3:6]
 if (type(row) is not dict or row.get('kind') != 'file'
   or type(row.get('path')) is not str
   or not row['path'].endswith('/importlib/_bootstrap.py')
   or row.get('logical_bytes') != 59507
   or not any(row is selected for selected in installation['rows'])
   or type(expected) is not bytes or type(reviewed) is not bytes
   or installation['files'].get(row['path']) is not expected
   or expected != reviewed
   or len(expected) != 59507 or not expected.isascii()
   or expected.count(b'\n') != 1570
   or _f._ordinary_data_size_v1(layout,'pointer') != 8):
  raise ValueError('BOOTSTRAP_STAGED_FULL_RAW_PROFILE_APPLICABILITY')
 source_profile = (59507, 1570, 5866, 10022, 15212, 202546, 2398, 2164, 2233, 23974, 15299, 114664, 3923)
 source_bytes, lines, nodes, fields, attrs, keychars, list_objects, list_slots, strings, stringchars, integers, integerbits, scalar_slots = source_profile
 obj2c_requests = ((16, 7), (24, 2005), (32, 270), (40, 257), (48, 66), (56, 2853), (64, 6), (72, 4), (80, 819), (88, 3), (96, 2), (104, 2), (112, 1), (448, 1))
 speculative_requests = ((24, 1106), (32, 564), (40, 4), (48, 381), (56, 45), (64, 107), (80, 13975), (88, 1607), (96, 100), (104, 27), (112, 5), (120, 240), (144, 1341), (152, 209), (168, 2113), (184, 61), (200, 285), (208, 729), (216, 906), (224, 130), (320, 1350), (376, 20), (392, 36), (408, 517), (920, 1), (1384, 9), (3912, 430), (8872, 289), (59912, 766))
 loop_rows = ((2, 8), (3, 5), (1, 1), (7, 6), (383, 1), (61, 21), (8, 1), (285, 23), (130, 26), (43, 2), (9, 1), (2, 1), (3, 4), (1, 1), (172, 1), (85, 1), (4, 4), (7, 1), (27, 11), (36, 17), (3, 1), (243, 9), (50, 19), (1, 1), (5, 4), (1, 1), (900, 25), (383, 7487), (98, 6), (258, 8), (173, 17), (5, 12), (36, 47), (503, 2), (1341, 16), (1350, 38), (1364, 9), (176, 19), (367, 4), (1, 1))
 helper_rows = (('BYTES', 4326, 251290), ('UNICODE', 23926, 1084873))
 code_rows = (('<module>', 13126, 548, 0, 100), ('<module>._object_name', 500, 53, 6, 17), ('<module>._wrap', 1336, 143, 2, 46), ('<module>._new_module', 353, 29, 0, 9), ('<module>._List', 100, 15, 0, 6), ('<module>._WeakValueDictionary', 1337, 58, 0, 7), ('<module>._WeakValueDictionary.__init__', 898, 72, 0, 28), ('<module>._WeakValueDictionary.__init__.KeyedRef', 1013, 53, 0, 11), ('<module>._WeakValueDictionary.__init__.KeyedRef.__new__', 587, 70, 0, 27), ('<module>._WeakValueDictionary.__init__.KeyedRef.__init__', 386, 39, 0, 13), ('<module>._WeakValueDictionary.__init__.KeyedRef.remove', 828, 119, 2, 44), ('<module>._WeakValueDictionary.clear', 304, 51, 0, 21), ('<module>._WeakValueDictionary._commit_removals', 829, 108, 7, 39), ('<module>._WeakValueDictionary.get', 857, 126, 8, 45), ('<module>._WeakValueDictionary.setdefault', 1060, 169, 8, 61), ('<module>._BlockingOnManager', 671, 29, 0, 5), ('<module>._BlockingOnManager.__init__', 135, 30, 0, 14), ('<module>._BlockingOnManager.__enter__', 692, 86, 0, 31), ('<module>._BlockingOnManager.__exit__', 266, 37, 0, 14), ('<module>._DeadlockError', 4, 0, 0, 1), ('<module>._has_deadlocked', 1523, 209, 5, 79), ('<module>._ModuleLock', 1076, 44, 0, 8), ('<module>._ModuleLock.__init__', 620, 112, 0, 47), ('<module>._ModuleLock.has_deadlock', 689, 62, 0, 24), ('<module>._ModuleLock.acquire', 2447, 344, 12, 113), ('<module>._ModuleLock.release', 1811, 268, 7, 90), ('<module>._ModuleLock.locked', 213, 22, 0, 8), ('<module>._ModuleLock.__repr__', 372, 52, 0, 15), ('<module>._DummyModuleLock', 752, 32, 0, 6), ('<module>._DummyModuleLock.__init__', 132, 30, 0, 13), ('<module>._DummyModuleLock.acquire', 123, 20, 0, 9), ('<module>._DummyModuleLock.release', 387, 58, 1, 20), ('<module>._DummyModuleLock.__repr__', 372, 52, 0, 15), ('<module>._ModuleLockManager', 570, 21, 0, 3), ('<module>._ModuleLockManager.__init__', 132, 30, 0, 13), ('<module>._ModuleLockManager.__enter__', 390, 53, 0, 20), ('<module>._ModuleLockManager.__exit__', 144, 21, 0, 8), ('<module>._get_module_lock', 2120, 273, 12, 89), ('<module>._get_module_lock.cb', 775, 113, 5, 38), ('<module>._lock_unlock_module', 598, 80, 6, 27), ('<module>._call_with_frames_removed', 314, 33, 0, 13), ('<module>._verbose_message', 1034, 145, 2, 51), ('<module>._requires_builtin', 561, 42, 0, 14), ('<module>._requires_builtin._requires_builtin_wrapper', 735, 87, 1, 29), ('<module>._requires_frozen', 561, 42, 0, 14), ('<module>._requires_frozen._requires_frozen_wrapper', 844, 90, 1, 30), ('<module>._load_module_shim', 1425, 182, 1, 69), ('<module>._module_repr', 2228, 305, 14, 90), ('<module>.ModuleSpec', 2822, 151, 0, 27), ('<module>.ModuleSpec.__init__', 614, 135, 2, 58), ('<module>.ModuleSpec.__repr__', 1579, 258, 2, 79), ('<module>.ModuleSpec.__eq__', 1155, 222, 6, 75), ('<module>.ModuleSpec.cached', 722, 143, 3, 50), ('<module>.ModuleSpec.cached', 69, 15, 0, 7), ('<module>.ModuleSpec.parent', 458, 78, 1, 27), ('<module>.ModuleSpec.has_location', 53, 10, 0, 5), ('<module>.ModuleSpec.has_location', 229, 27, 0, 10), ('<module>.spec_from_loader', 3050, 391, 14, 132), ('<module>._spec_from_module', 3111, 536, 37, 181), ('<module>._init_module_attrs', 5376, 874, 54, 277), ('<module>.module_from_spec', 1668, 200, 3, 68), ('<module>._module_repr_from_spec', 2184, 402, 6, 123), ('<module>._exec', 4490, 593, 12, 206), ('<module>._load_backward_compatible', 3756, 548, 29, 181), ('<module>._load_unlocked', 3680, 537, 20, 186), ('<module>._load', 530, 56, 4, 17), ('<module>.BuiltinImporter', 2857, 179, 0, 40), ('<module>.BuiltinImporter.find_spec', 607, 63, 1, 23), ('<module>.BuiltinImporter.create_module', 835, 112, 1, 39), ('<module>.BuiltinImporter.exec_module', 308, 33, 0, 12), ('<module>.BuiltinImporter.get_code', 50, 10, 0, 4), ('<module>.BuiltinImporter.get_source', 50, 10, 0, 4), ('<module>.BuiltinImporter.is_package', 50, 10, 0, 4), ('<module>.FrozenImporter', 4051, 230, 0, 43), ('<module>.FrozenImporter._fix_up_module', 8236, 1207, 20, 428), ('<module>.FrozenImporter._resolve_filename', 2746, 471, 13, 156), ('<module>.FrozenImporter.find_spec', 2407, 273, 2, 103), ('<module>.FrozenImporter.create_module', 581, 100, 7, 39), ('<module>.FrozenImporter.exec_module', 728, 91, 0, 36), ('<module>.FrozenImporter.load_module', 1650, 209, 1, 78), ('<module>.FrozenImporter.get_code', 233, 27, 0, 10), ('<module>.FrozenImporter.get_source', 50, 10, 0, 4), ('<module>.FrozenImporter.is_package', 233, 27, 0, 10), ('<module>._ImportLockContext', 590, 26, 0, 4), ('<module>._ImportLockContext.__enter__', 144, 21, 0, 8), ('<module>._ImportLockContext.__exit__', 144, 21, 0, 8), ('<module>._resolve_name', 1121, 163, 3, 53), ('<module>._find_spec', 3120, 428, 22, 150), ('<module>._sanity_check', 2120, 270, 6, 83), ('<module>._find_and_load_unlocked', 6014, 845, 26, 291), ('<module>._find_and_load', 3406, 398, 8, 128), ('<module>._gcd_import', 1102, 112, 1, 38), ('<module>._handle_fromlist', 3450, 459, 13, 150), ('<module>._calc___package__', 2373, 360, 4, 118), ('<module>.__import__', 3395, 434, 7, 147), ('<module>._builtin_from_name', 731, 92, 1, 31), ('<module>._setup', 3351, 448, 7, 167), ('<module>._install', 734, 82, 0, 30), ('<module>._install_external_importers', 385, 52, 0, 24))
 parser_core = _f._ordinary_runtime7_bootstrap_parser_core_request_v1(layout,expected,lines)
 if parser_core['memo_count'] != 57*parser_core['tokens']:
  raise ValueError('BOOTSTRAP_STAGED_ORIGINAL_MEMO_PASSES')
 names, numbers, namechars, maxname = 6773,59,46078,27
 speculative = _f._ordinary_runtime7_bootstrap_arena_request_v1(layout,
  speculative_requests+((56,names+numbers),),28252+names+numbers)
 helper_python = 0
 for family,count,extent in helper_rows:
  prefix = _f._ordinary_data_size_v1(layout,'bytes_prefix' if family=='BYTES' else 'unicode_prefix')
  helper_python += count*prefix + (extent if family=='BYTES' else 8*extent)
 loop_arrays = sum(3*8*count*(span+1) for count,span in loop_rows)
 leaf_python = (names*_f._ordinary_data_size_v1(layout,'unicode_prefix')
  +4*(namechars+names)+numbers*28
  +_f._ordinary_data_dict_requests_v1(layout,1,names))
 leaf_transient = _f._ordinary_data_unicode_request_v1(layout,maxname)
 parser = parser_core['parser_core_request']+speculative+helper_python+loop_arrays+leaf_python+leaf_transient
 keys=fields+attrs
 ast_request = (nodes*(24+_f._ordinary_data_size_v1(layout,'gc'))
  +_f._ordinary_data_dict_requests_v1(layout,nodes,keys)
  +_f._ordinary_data_list_requests_v1(layout,list_objects,list_slots)
  +keys*_f._ordinary_data_size_v1(layout,'unicode_prefix')+4*(keychars+keys)
  +strings*_f._ordinary_data_size_v1(layout,'unicode_prefix')+4*(stringchars+strings)
  +integers*_f._ordinary_data_size_v1(layout,'int_prefix')
  +_f._ordinary_data_size_v1(layout,'int_digit_bytes')*((integerbits
   +_f._ordinary_data_size_v1(layout,'int_digit_bits')-1)
   //_f._ordinary_data_size_v1(layout,'int_digit_bits')+2*integers))
 obj2c = _f._ordinary_runtime7_bootstrap_arena_request_v1(layout,obj2c_requests,scalar_slots)
 def capacity(value,initial):
  result=initial
  while result<value: result*=2
  return result
 instruction_sequences = 0
 cfg_max = assembly_max = retained_codes = 0
 for name,I,L,J,V in code_rows:
  instruction_sequences += (72+44*(capacity(I,100)+capacity(I,100)//2)
   +4*(capacity(L+1,10)+capacity(L+1,10)//2))
  F=I+(I+4)*J+2*V+3
  blocks=I+J+L+1
  capacities=16*blocks+2*F
  cfg=(40*(capacities+capacities//2)
   +blocks*(72+192+8)+8*(L+1)+16*max(1,V)
   +F+16*3*max(1,F)+4*max(1,F))
  cfg_max=max(cfg_max,cfg)
  codebytes,linebytes,exceptionbytes=26*F,22*F,20*F
  buffers=sum(3*capacity(n,initial)//2 for n,initial in
   ((codebytes,128),(linebytes,32),(exceptionbytes,16)))
  retained_codes += (3*_f._ordinary_data_size_v1(layout,'bytes_prefix')
   +codebytes+linebytes+exceptionbytes+320+codebytes+32)
  assembly_max=max(assembly_max,buffers)
 units=len(code_rows);symbols=units+1;depth=6
 key_bound=strings+387+5*units+36
 dictionary_objects=6*depth+symbols+depth+3
 dictionary_keys=(6*depth+symbols+depth+2)*key_bound+symbols
 dictionary_request=_f._ordinary_data_dict_requests_v1(layout,dictionary_objects,dictionary_keys,general=True)
 set_objects=9*depth+3+depth+1
 set_request=set_objects*(216+2*16*(8+8*key_bound))
 list_request=_f._ordinary_data_list_requests_v1(layout,3*symbols+depth+3,(3*symbols+depth+3)*key_bound)
 tuple_request=(6*units*_f._ordinary_data_tuple_request_v1(layout,key_bound)
  +units*_f._ordinary_data_bytes_request_v1(layout,key_bound))
 string_request=(units*_f._ordinary_data_unicode_request_v1(layout,source_bytes)
  +2*units*_f._ordinary_data_unicode_request_v1(layout,stringchars))
 integer_request=dictionary_keys*(_f._ordinary_data_size_v1(layout,'int_prefix')
  +5*_f._ordinary_data_size_v1(layout,'int_digit_bytes'))
 native_units=units*(1024+72+32)+symbols*(256+80)+88
 components=(('instruction_sequences',instruction_sequences),
  ('cfg_all_blocks_arrays_stacks_and_maps',cfg_max),
  ('compiler_and_symbol_dictionaries',dictionary_request),
  ('symtable_and_class_sets',set_request),('compiler_lists',list_request),
  ('code_tuples',tuple_request),('compiler_strings_and_doc_intermediates',string_request),
  ('compiler_index_integers',integer_request),('native_fixed_units',native_units),
  ('assembly_buffers_and_retained_code',retained_codes+assembly_max))
 compiler=sum(request for name,request in components)
 raw_and_text=(_f._ordinary_data_bytes_request_v1(layout,source_bytes)
  +_f._ordinary_data_unicode_request_v1(layout,source_bytes))
 stages=(('AST1',raw_and_text+parser+ast_request),
  ('AST2',raw_and_text+parser+2*ast_request),
  ('COMPILE',raw_and_text+2*ast_request+obj2c+compiler))
 return dict(original_installation=installation,original_profile=profile,
  original_expected_source=expected,profile_producer=producer,
  source_profile=source_profile,obj2c_requests=obj2c_requests,
  parser_core=parser_core,parser_request=parser,python_ast_request=ast_request,
  obj2c_arena_request=obj2c,compiler_components=components,
  compiler_request=compiler,retained_source_request=raw_and_text,
  stage_requests=stages,staged_request=max(request for stage,request in stages))


def _facet_fn_bootstrap_fixed_constructor_request_v1(layout, value, name, *, receiver, native_root):
 import tools.validation_reliability as _f
 if (type(value) is not dict or type(name) is not str or not name
   or type(receiver) is not bool or _f._ordinary_data_size_v1(layout,'pointer') != 8
   or _f._ordinary_data_size_v1(layout,'gc') != 16
   or type(value.get('repository')) is not str
   or type(value.get('environment')) is not dict
   or set(value['environment']) != {'GITHUB_ACTIONS','GITHUB_EVENT_NAME',
    'GITHUB_REPOSITORY','GITHUB_WORKSPACE','GITHUB_EVENT_PATH','RUNNER_TEMP',
    'GITHUB_REF','GITHUB_REF_NAME','GITHUB_SHA','GITHUB_HEAD_REF','GITHUB_BASE_REF',
    'GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'}
   or not all(type(v) is str for v in value['environment'].values())):
  raise ValueError('BOOTSTRAP_FIXED_ORIGINAL_TYPED_INPUTS_AND_LP64_LAYOUT')
 p=_f._ordinary_data_size_v1(layout,'pointer')
 gc=_f._ordinary_data_size_v1(layout,'gc')
 classes=(_f._LinuxPreflightQueriesV1,_f._LinuxPreflightScopeV1,_f._LinuxSourceNativeV2)
 instance_requests=[]
 for cls,fields in zip(classes,(30,102,5)):
  if (type(cls) is not type or len(cls.__bases__) != 1
    or cls.__bases__[0] is not object
    or '__slots__' in cls.__dict__ or '__new__' in cls.__dict__
    or cls.__itemsize__ != 0 or cls.__basicsize__ != 2*p
    or cls.__flags__ & ((1<<14)|(1<<2)|(1<<3)|(1<<4))
     != ((1<<14)|(1<<2)|(1<<3)|(1<<4))):
   raise ValueError('BOOTSTRAP_FIXED_ORIGINAL_CONSTRUCTOR_TYPE_ABI')
  inline=_f._ordinary_data_align_v1(30,p)+(30+1)*p
  instance_requests.append((cls,cls.__init__,cls.__init__.__code__,fields,
   cls.__basicsize__+gc+2*p+inline
    +_f._ordinary_data_dict_requests_v1(layout,1,fields)))
 fixed_containers=(_f._ordinary_data_list_requests_v1(layout,11,0)
  +_f._ordinary_data_dict_requests_v1(layout,2,0)+216
  +_f._ordinary_data_dict_requests_v1(layout,1,4))
 host_containers=_f._ordinary_data_dict_requests_v1(layout,5,104)
 ceiling_containers=_f._ordinary_data_dict_requests_v1(layout,5,60)
 bootstrap_containers=(_f._ordinary_data_dict_requests_v1(layout,1,13)
  +_f._ordinary_data_dict_requests_v1(layout,1,2)
  +_f._ordinary_data_dict_requests_v1(layout,1,7)
  +_f._ordinary_data_dict_requests_v1(layout,1,9)
  +_f._ordinary_data_tuple_request_v1(layout,6)
  +9*_f._ordinary_data_tuple_request_v1(layout,2)
  +_f._ordinary_data_tuple_request_v1(layout,9))
 native_type=_f.Path.__new__.__globals__['PosixPath']
 if type(native_root) is not native_type:
  raise ValueError('BOOTSTRAP_FIXED_ORIGINAL_NATIVE_ROOT_TYPE')
 raw_root=native_root._raw_paths
 if (type(raw_root) is not list or not raw_root
   or not all(type(part) is str and '\0' not in part for part in raw_root)):
  raise ValueError('BOOTSTRAP_FIXED_ORIGINAL_NATIVE_ROOT_OPERANDS')
 root_operands=len(raw_root)
 root_len=sum(len(part) for part in raw_root)+root_operands
 prefix_len=root_len+7+(9 if receiver else 0)
 prefix_operands=root_operands+1+(1 if receiver else 0)
 paths=[('native_root/prefix',root_operands+1,root_len+7)]
 if receiver: paths.append(('prefix/receiver',root_operands+2,prefix_len))
 paths.extend((('prefix/query',prefix_operands+1,prefix_len+6),
  ('Queries.Path(evidence_root)',prefix_operands+1,prefix_len+6),
  ('eligibility.Path(repository)',1,len(value['repository'])),
  ('prefix/control',prefix_operands+1,prefix_len+8),
  ('native_root/runtime',root_operands+1,root_len+8),
  ('prefix/run-evidence',prefix_operands+1,prefix_len+13),
  ('Scope.Path(control)',prefix_operands+1,prefix_len+8),
  ('Scope.Path(runtime)',root_operands+1,root_len+8),
  ('Scope.Path(private_root)',root_operands,root_len),
  ('Scope.Path(spool)',prefix_operands+1,prefix_len+13),
  ('control/installation',prefix_operands+2,prefix_len+21),
  ('runtime/payload',root_operands+2,root_len+16),
  ('geometry.Path(root_witness)',1,1),
  ('geometry.root/validation-output',root_operands+1,root_len+18),
  ('geometry.root/pytest-root',root_operands+1,root_len+12)))
 path_requests=[]
 for label,operands,extent in paths:
  request=(11*p+gc
   +_f._ordinary_data_list_requests_v1(layout,4,operands+3*(extent+1))
   +2*((extent+1)*_f._ordinary_data_size_v1(layout,'unicode_prefix')
    +4*(extent+(extent+1)))
   +(2*operands+6)*_f._ordinary_data_unicode_request_v1(layout,extent)
   +4*_f._ordinary_data_tuple_request_v1(layout,operands+2)
   +_f._ordinary_data_dict_requests_v1(layout,1,0)
   +_f._ordinary_data_tuple_request_v1(layout,3))
  path_requests.append((label,operands,extent,request))
 components=(('original_query_scope_native_instance_headers',
  sum(row[4] for row in instance_requests)),
  ('original_fixed_empty_and_adoption_containers',fixed_containers),
  ('original_host_meter_containers',host_containers),
  ('original_ceiling_containers',ceiling_containers),
  ('original_bootstrap_containers',bootstrap_containers),
  ('original_fixed_paths',sum(row[3] for row in path_requests)))
 return dict(original_value=value,original_name=name,receiver=receiver,
  original_native_root=native_root,original_raw_root=raw_root,
  original_root_values=tuple(raw_root),root_extent_bound=root_len,
  constructor_sources=tuple(instance_requests),path_sources=tuple(path_requests),
  components=components,fixed_request=sum(request for component,request in components),
  remaining_original_source_components=('manifest_and_per_selected_row_classifiers',
   'event_json_and_input_objects','new_name_cutoff_and_key_objects',
   'call_frame_and_retained_failure_objects','ctypes_library_and_initialized_wrappers',
   'whole_source_parsers_compiler_and_stage_ledger'))


def _facet_fn_initial_manager_origin_v1(raw, *, unit, control_group, invocation):
    """Decode one actual fixed ancestor observation, never issue birth custody.

    The original native caller owns the real receipt, both complete streams,
    held ancestor and manager generation. It obtains this timestamp BEFORE the
    selected controller request and rereads that same generation later. These
    observations are separate from the unchanged six-field COMMON/suffix rows.
    """
    import tools.validation_reliability as _f
    fields = ('Id', 'LoadState', 'Transient', 'InvocationID', 'ControlGroup',
     'ActiveState', 'ActiveEnterTimestampMonotonic')
    _f._preflight_require_v1(type(raw) is bytes and 0 < len(raw) <= 4096
     and raw.endswith(b'\n') and b'\r' not in raw and b'\0' not in raw
     and all(value < 128 for value in raw)
     and type(unit) is str and _f.re.fullmatch(r'[A-Za-z0-9_-]{1,128}\.slice', unit)
     and type(control_group) is str and control_group.startswith('/')
     and control_group != '/' and control_group.rsplit('/', 1)[-1] == unit
     and type(invocation) is str and _f.re.fullmatch(r'[0-9a-f]{32}', invocation),
     'ORDINARY_ORIGINAL_ANCESTOR_MANAGER_OBSERVATION')
    observed = {}
    for line in raw[:-1].split(b'\n'):
     key, delimiter, value = line.partition(b'=')
     name = key.decode('ascii')
     _f._preflight_require_v1(delimiter == b'=' and name in fields
      and name not in observed and value and b'=' not in value,
      'ORDINARY_ORIGINAL_ANCESTOR_MANAGER_FIELD')
     observed[name] = value.decode('ascii')
    _f._preflight_require_v1(set(observed) == set(fields)
     and observed['Id'] == unit and observed['LoadState'] == 'loaded'
     and observed['Transient'] == 'yes' and observed['ActiveState'] == 'active'
     and observed['InvocationID'] == invocation
     and observed['ControlGroup'] == control_group,
     'ORDINARY_SAME_ORIGINAL_ACTIVE_ANCESTOR_GENERATION')
    spelling = observed['ActiveEnterTimestampMonotonic']
    _f._preflight_require_v1(_f.re.fullmatch(r'[1-9][0-9]{0,19}', spelling) is not None,
     'ORDINARY_ORIGINAL_ANCESTOR_MONOTONIC_TIMESTAMP')
    microseconds = int(spelling)
    _f._preflight_require_v1(microseconds <= ((1 << 64) - 1) // 1000,
     'ORDINARY_ORIGINAL_ANCESTOR_TIMESTAMP_OVERFLOW')
    origin = microseconds * 1000
    _f._preflight_require_v1(origin <= (1 << 64) - 1 - 3720 * 10**9,
     'ORDINARY_ORIGINAL_ANCESTOR_CUTOFF_OVERFLOW')
    return observed, origin


def _ordinary_ci_bootstrap_stage_source_request_v1(runner, product, stage):
 """Project the same initialized originals; never fund the earlier prefix."""
 import tools.validation_reliability as _f
 from types import CodeType,FunctionType,ModuleType
 if type(product)is not dict or type(stage)is not str or stage not in ('PREPARE','QUERY'):
  raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_PRODUCT_AND_STAGE')
 fields=('native_input','native_hold','native_generation','startup','source_generation',
  'roles','actor','phase','role','native_root','origin_ns','errors')
 original=product.get('original')
 if (type(original)is not tuple or len(original)!=13 or original[0]is not product
  or any(original[i+1]is not product.get(name)for i,name in enumerate(fields))):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_NATIVE13')
 source=product['source_generation'];native=product['native_generation'];errors=product['errors']
 hold=product['native_hold']
 if type(source)is not dict or type(native)is not dict or type(hold)is not dict or type(errors)is not list or errors:
  raise ValueError('ORDINARY_STAGE_SOURCE_CLOSED_ORIGINAL_CARRIERS')
 so=source.get('original');no=native.get('original');value=product['native_input']
 if (type(value)is not dict or type(so)is not tuple or len(so)!=17 or so[0]is not source
  or so[1]is not value or so[16]is not errors or so[8]is not _f or so[9]is not _f.__dict__
  or type(runner)is not ModuleType or so[3]is not runner or so[4]is not runner.__dict__
  or type(no)is not tuple or len(no)!=10 or no[0]is not native or no[1]is not value
  or no[2]is not source or no[9]is not errors):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_SOURCE17_NATIVE10')
 names=('native_input','entry_original','runner','namespace','initializer','entry','entry_code',
  'module','module_namespace','native_method','native_method_code','code_paths','workflow',
  'expected_module_closure','physical_observations','errors')
 if (any(so[i+1]is not source.get(name)for i,name in enumerate(names))
  or any(no[i+1]is not native.get(name)for i,name in enumerate(('native_input','source_generation',
   'native_class','constructor','constructor_code','native_method','native_method_code',
   'physical_observations','errors')))):
  raise ValueError('ORDINARY_STAGE_SOURCE_UNCHANGED_SOURCE17_NATIVE10_FIELDS')
 issuer=value.get('native_product_attempt');issue=value.get('initial_request_issuer')
 if type(issuer)is not dict or type(issue)is not dict:
  raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_ISSUERS')
 io=issuer.get('original');entry=value.get('entry_original')
 if (type(io)is not tuple or len(io)!=9 or type(entry)is not tuple or len(entry)!=9
  or io[0]is not issuer or io[1]is not issuer.get('entry_attempt')or io[1]is not entry[0]
  or io[2]is not hold.get('owner')or io[3]is not errors
  or io[4]is not product['phase']or io[5]is not runner or io[6]is not so[5]
  or io[7]is not so[6]or io[8]is not so[7]or so[2]is not entry):
  raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_NATIVE69_ISSUER9')
 initialized=issuer.get('initialized_original');profile=value.get('early_profile')
 allocation=value.get('early_allocation_original');issued=issue.get('result_original')
 if (type(initialized)is not tuple or len(initialized)!=14 or initialized[0]is not issuer
  or initialized[1]is not value or initialized[11]is not profile or initialized[12]is not allocation
  or initialized[13]is not errors or issuer.get('native_product')is not product
  or issuer.get('native_input')is not value or issuer.get('stage')!='STAGE_REQUESTS'
  or type(profile)is not tuple or len(profile)!=12 or profile[0]is not value
  or profile[1]is not source or profile[2]is not native or profile[6]is not None
  or type(allocation)is not tuple or len(allocation)!=4 or allocation[0]is not value
  or allocation[1]is not profile or type(allocation[2])is not dict or type(allocation[3])is not dict
  or type(issued)is not tuple or len(issued)!=7 or issued[0]is not issue
  or issued[4]is not allocation or issued[5]is not allocation[3] or issued[6]is not profile
  or issue.get('complete')is not True or issued[2]is not profile[7]
  or type(issued[3])is not tuple or len(issued[3])!=6
  or any(type(row)is not tuple or len(row)!=2 or type(row[0])is not str
   or type(row[1])is not int or row[1]<0 for row in issued[3])
  or tuple(allocation[2].items())!=issued[3]
  or tuple(allocation[3])!=tuple(name for name,_ in issued[3])
  or any(type(amount)is not int or amount<0 for amount in allocation[3].values())):
  raise ValueError('ORDINARY_STAGE_SOURCE_UNCHANGED_INITIAL12_FROZEN_SIX_POOLS')
 startup=profile[3];startup_original=startup.get('original')if type(startup)is dict else None
 if (type(startup)is not dict or type(startup_original)is not tuple or len(startup_original)!=12
  or startup_original[0]is not startup or any(a is not b for a,b in zip(startup_original[1:],
   (value,source,native,product['phase'],source['code_paths'],source['workflow'],
    startup.get('expected_startup_keys'),startup.get('expected_basis_keys'),startup.get('expected_roles'),
    startup.get('physical_observations'),errors)))or startup.get('startup_binding')is not product['startup']
  or startup.get('roles')is not product['roles']):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_ORIGINAL_STARTUP12_CLOSED_STARTUP9')
 abi,layout,storage,success=initialized[3],initialized[4],initialized[6],initialized[7]
 physical=issuer.get('physical')
 if (type(physical)is not dict or initialized[2]is not issuer.get('native')
  or initialized[8]is not physical or initialized[9]is not physical.get('original')
  or initialized[10]is not physical.get('result_original')
  or physical is not value.get('current_native_observation')or physical.get('complete')is not True
  or physical.get('pending')is not False or physical.get('errors')is not errors
  or physical.get('native')is not initialized[2]or physical.get('native_input')is not value
  or type(hold)is not dict or issuer.get('hold')is not hold or hold.get('errors')is not errors
  or hold.get('source_generation')is not source or hold.get('native_generation')is not native
  or hold.get('startup')is not product['startup']or hold.get('native_input')is not value
  or type(abi)is not tuple or len(abi)!=2 or type(abi[0])is not dict or type(abi[1])is not tuple
  or abi is not issuer.get('abi_observation')or initialized[5]is not issuer.get('storage_data_request')):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_PHYSICAL_HOLD_AND_ABI_ORIGINALS')
 hold_names=('owner','service_unit','invocation','holder_identity','holder_pidfd_slot','holder_cgroup',
  'holder_cgroup_slot','holder_events_slot','ancestor_cgroup','ancestor_slot','cutoffs','errors',
  'holder_kernel_observations','native_input','native_generation','source_generation','startup')
 hold_original=hold.get('original')
 attempts=value.get('initialized_storage_attempts')
 if (type(hold_original)is not tuple or len(hold_original)!=18 or hold_original[0]is not hold
  or any(hold_original[i+1]is not hold.get(name)for i,name in enumerate(hold_names))
  or hold['cutoffs']is not issuer.get('original_cutoffs')or type(attempts)is not list
  or len(attempts)!=1 or storage is not attempts[0]):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_NATIVE_HOLD18_AND_SOLE_GETTER')
 frozen=layout.get('original')if type(layout)is dict else None
 before=storage.get('original')if type(storage)is dict else None
 if (type(layout)is not dict or layout is not issuer.get('initial_layout')
  or layout.get('initial_observation')is not abi
  or type(frozen)is not tuple or len(frozen)!=4 or frozen[0]is not abi
  or frozen[1]is not abi[0]or frozen[2]is not abi[1]or frozen[3]is not layout.get('sizes')
  or any(type(key)is not str or type(amount)is not int or amount<=0 for key,amount in abi[0].items())
  or tuple(abi[0].items())!=frozen[3]or layout.get('tiny_layout_observations')is not abi[1]
  or type(storage)is not dict or storage is not issuer.get('initialized_storage')
  or type(before)is not tuple or len(before)!=7 or before[0]is not storage
  or any(a is not b for a,b in zip(before[1:],(initialized[2],storage.get('owner'),
   storage.get('path'),storage.get('deadline_ns'),storage.get('requests'),storage.get('errors'))))
  or storage.get('success_original')is not success or type(success)is not tuple or len(success)!=14
  or success[0]is not storage or any(a is not b for a,b in zip(success[1:],
   (initialized[2],storage.get('owner'),storage.get('path'),storage.get('path_before'),
    storage.get('handle_before'),storage.get('path_after'),storage.get('handle_after'),
    storage.get('raw'),storage.get('entries'),storage.get('mapped_extent'),storage.get('requests'),
    storage.get('errors'),storage.get('deadline_ns'))))or storage.get('complete')is not True
  or storage.get('closed')is not True or storage['errors']
  or type(storage['mapped_extent'])is not int or storage['mapped_extent']<=0):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_ABI_LAYOUT_AND_GETTER22_SUCCESS14')
 acquisition=source.get('source_input4_acquisition');binding=source.get('native_input_binding')
 if (type(acquisition)is not dict or type(binding)is not dict or acquisition.get('complete')is not True
  or acquisition.get('result')is not binding or binding.get('complete')is not True
  or binding.get('inputs')is not source.get('protected_inputs')or binding.get('physical')is not physical
  or acquisition.get('generation')is not source or acquisition.get('errors')is not errors
  or type(acquisition.get('code_observations'))is not list):
  raise ValueError('ORDINARY_STAGE_SOURCE_SAME_COMPLETE_INPUT4_CODE_BINDINGS')
 roots_by_module={}
 for module in (runner,_f,_f.sys.modules.get('tools.validation_scope_registry'),_f.sys.modules.get(__name__)):
  if type(module)is not ModuleType:
   raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_LOADED_MODULE')
  matches=[]
  for note in acquisition['code_observations']:
   if type(note)is not dict:
    raise ValueError('ORDINARY_STAGE_SOURCE_EXACT_CODE_NOTE')
   if note.get('module')is module:matches.append(note)
  if len(matches)!=1:
   raise ValueError('ORDINARY_STAGE_SOURCE_ONE_INDEPENDENT_MODULE_CODE')
  note=matches[0];old=note.get('original');root=note.get('root')
  expected=(note,note.get('record'),module,module.__dict__,root,note.get('witness'),
   note.get('witness').__code__ if type(note.get('witness'))is FunctionType else None,
   note.get('raw'),note.get('compiled'),note.get('filename'),note.get('proof_kind'))
  if (type(old)is not tuple or len(old)!=11 or any(a is not b for a,b in zip(old,expected))
   or note.get('complete')is not True or note.get('whole_initializer')is not True
   or type(root)is not CodeType or root is not module.__dict__.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')
   or type(note.get('compiled'))is not CodeType or type(note.get('raw'))is not bytes
   or not _f._ordinary_control_code_source_equal_v1(note['compiled'],root)):
   raise ValueError('ORDINARY_STAGE_SOURCE_UNCHANGED_PROTECTED_WHOLE_CODE')
  roots_by_module[module]=root
 producers=(runner.__dict__.get('_ordinary_bootstrap_heap_prepare_request_v1'),
  runner.__dict__.get('_ordinary_bootstrap_query_request_v1'))
 facade=runner.__dict__.get('_ordinary_bootstrap_initial_stage_source_request_v1')
 controls=tuple(runner.__dict__.get(name)for name in ('_ordinary_bootstrap_request_begin_v1',
  '_ordinary_bootstrap_request_finish_v1','_ordinary_bootstrap_request_fail_v1'))
 functions=(*producers,facade,*controls)
 if (any(type(fn)is not FunctionType or fn.__globals__ is not runner.__dict__
   or fn.__closure__ is not None for fn in functions)
  or runner.__dict__.get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')is not so[5]
  or type(so[5])is not CodeType or not all(any(code is fn.__code__ for code in so[5].co_consts)
   for fn in functions)):
  raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_RUN_FUNCTION_CODES')
 pre=profile[3].get('pre_cold_result')if type(profile[3])is dict else None
 ci=pre.get('ci_source_code_original')if type(pre)is dict else None
 if (type(ci)is not tuple or len(ci)!=8 or ci[0]is not pre or type(ci[1])is not ModuleType
  or ci[2]is not globals()or ci[1].__dict__ is not ci[2]
  or type(ci[3])is not CodeType or ci[3]is not globals().get('_ORDINARY_INITIALIZED_MODULE_CODE_V1')
  or type(ci[4])is not CodeType or not _f._ordinary_control_code_source_equal_v1(ci[4],ci[3])
  or not any(code is _ordinary_ci_bootstrap_stage_source_request_v1.__code__ for code in ci[3].co_consts)
  or pre.get('complete')is not True):
  raise ValueError('ORDINARY_STAGE_SOURCE_PROTECTED_COMPLETE_CI_CODE')
 caller=_f.sys._getframe(1);parent=_f.sys._getframe(2)
 try:
  if (caller.f_code is not facade.__code__ or caller.f_globals is not runner.__dict__
   or caller.f_locals.get('product')is not product or caller.f_locals.get('stage')is not stage
   or parent.f_code is not so[11] or parent.f_globals is not so[9]
   or parent.f_locals.get('product')is not product or parent.f_locals.get('issuer')is not issuer):
   raise ValueError('ORDINARY_STAGE_SOURCE_REACHED_NATIVE69_ORIGINAL_CALLER')
 finally:del caller,parent
 stages=issue.get('stage_requests')
 if stages is None:
  stages={};issue['stage_requests']=stages
 if type(stages)is not dict or stage in stages or (stage=='QUERY'and 'PREPARE'not in stages):
  raise ValueError('ORDINARY_STAGE_SOURCE_ONE_PREPARE_THEN_PURE_QUERY')
 producer=producers[0 if stage=='PREPARE'else 1]
 record=dict(stage=stage,product=product,issuer=issuer,initialized_original=initialized,
  source_original=so,native_original=no,initial_original=issued,allocation=allocation,
  producer=producer,producer_code=producer.__code__,errors=errors,parts=None,request=None)
 stages[stage]=record
 record['original']=(record,stage,product,issuer,initialized,so,no,issued,allocation,
  producer,producer.__code__,errors)
 # Every value below is a demand for this later fixed request construction.
 # Current VM is charged once in PREPARE; it grants nothing to earlier work.
 T=lambda n:_f._ordinary_data_tuple_request_v1(layout,n)
 D=lambda n,k:_f._ordinary_data_dict_requests_v1(layout,n,k,general=False)
 data_functions=[]
 for module,prefix in ((_f,'_ordinary_data_'),(_f.sys.modules['tools.validation_scope_registry'],'_facet_fn_data_')):
  for name in ('align_v1','size_v1','tuple_request_v1','list_requests_v1','dict_requests_v1'):
   function=module.__dict__.get(prefix+name)
   if (type(function)is not FunctionType or function.__globals__ is not module.__dict__
    or not any(code is function.__code__ for code in roots_by_module[module].co_consts)):
    raise ValueError('ORDINARY_STAGE_SOURCE_FIXED_ORIGINAL_DATA_CALLEES')
   data_functions.append(function)
 roots=tuple(fn.__code__ for fn in (*functions,*data_functions,_ordinary_ci_bootstrap_stage_source_request_v1))+(so[11],)
 if any(type(code)is not CodeType for code in roots):
  raise ValueError('ORDINARY_STAGE_SOURCE_FIXED_FRAME_CODES')
 codes=[];pending=list(roots)
 while pending:
  code=pending.pop()
  if any(code is old for old in codes):continue
  codes.append(code)
  pending.extend(item for item in code.co_consts if type(item)is CodeType)
 codes=tuple(codes)
 frame_slots=sum(code.co_nlocals+code.co_stacksize+len(code.co_cellvars)+len(code.co_freevars)for code in codes)
 frames=len(codes)*(72+80+16)+8*frame_slots
 closures=2*(len(codes)*(152+16+48)+8*frame_slots+frame_slots*(24+16))
 # Emitter/body errors, the original failure witness, three saved-list
 # recording errors and the Native caller's aggregation are fixed branches.
 # Eight complete Source frame/traceback closures cover them together.
 failures=8*(frames+len(codes)*(40+16)+112+T(3))
 count=3 if stage=='PREPARE'else 2
 records=D(1,15)+D(1,2)+D(1,8)+T(12)+T(10)+T(count)+count*T(2)+T(count)+T(len(codes))
 records+=2*T(7)+T(9)+T(5)+T(11)
 records+=_f._ordinary_data_dict_requests_v1(layout,1,4,general=True)
 records+=_f._ordinary_data_list_requests_v1(layout,2,2*len(codes))+T(len(roots))
 records+=_f._ordinary_data_list_requests_v1(layout,4,4)+T(len(data_functions))
 records+=frame_slots*_f._ordinary_data_size_v1(layout,'control_integer')
 # Exact tuple/dict/frame requests include their object prefixes. The getter
 # observes existing native stack/allocator backing; no map multiplier or
 # predicted native allocator growth is a new QTT allocation request.
 entries=storage['entries']
 if (type(entries)is not tuple or not entries or any(type(row)is not tuple or len(row)!=7
  or any(type(row[i])is not int or row[i]<0 for i in (0,1,3,4,5,6))
  or type(row[2])is not bytes or len(row[2])!=4 or row[1]<=row[0]for row in entries)
  or sum(row[1]-row[0]for row in entries)!=storage['mapped_extent']):
  raise ValueError('ORDINARY_STAGE_SOURCE_ORIGINAL_COMPLETE_MAPPING_ROWS')
 parts=(('original_request_emitter_and_stage_records',records),
  ('original_selected_call_frames_and_retained_failures',frames+closures+failures))
 if stage=='PREPARE':parts+=(('original_interpreter_and_prior_intern_storage',storage['mapped_extent']),)
 retained=tuple(name for name,_ in parts)
 request=(product,source,native,product['startup'],layout,parts,retained,
  producer,producer.__code__,product['native_root'])
 record['parts']=parts;record['request']=request
 record['result_original']=(record,record['original'],parts,retained,request,initialized,issued)
 return request
