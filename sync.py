from webdav3.client import Client
import os
import json
import dateutil
import time
import hashlib
import tempfile
import merge3


class WebDavSync:
    client = None
    _journal_path = ".brorg_journal.json"

    local = None
    remote = None
    journal = None

    def __init__(self, host: str, login: str, passwd: str, root: str, local_path: str):
        options = {
            "webdav_hostname": host,
            "webdav_login": login,
            "webdav_password": passwd,
            "webdav_root": root,
        }
        self.client = Client(options)
        self.remote_path = root
        self.local_path = local_path

    def _get_remote_etag(self, remote_path):
        return self.client.info(remote_path)["etag"].strip("\"'")

    def _compute_local_etag(local_path):
        with open(local_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        return file_hash.hexdigest()

    def _receive(self, relpath):
        print("receiving {}".format(relpath))
        local_pth = os.path.join(self.local_path, relpath)

        try:
            os.makedirs(os.path.dirname(local_pth))
        except Exception:
            pass
        self.client.download_sync(remote_path=relpath, local_path=local_pth)
        di = {
            "remote_etag": self.remote[relpath]["etag"].strip("'\""),
            "local_etag": WebDavSync._compute_local_etag(local_pth),
            "relpath": relpath,
        }
        with open(local_pth, "r") as fh:
            try:
                di["content"] = fh.read()
            except UnicodeDecodeError:
                di["content"] = None
        self.journal[relpath] = di
        self._save_journal()

    def _send(self, relpath):
        print("sending {}".format(relpath))
        local_pth = os.path.join(self.local_path, relpath)

        pths = os.path.dirname(relpath)
        for pth in pths.split("/"):
            if not self.client.check(pth):
                self.client.mkdir(pth)

        self.client.upload_sync(remote_path=relpath, local_path=local_pth)
        di = {
            "local_etag": self.local[relpath]["etag"].strip("'\""),
            "remote_etag": self._get_remote_etag(relpath),
            "relpath": relpath,
        }
        with open(local_pth, "r") as fh:
            try:
                di["content"] = fh.read()
            except UnicodeDecodeError:
                di["content"] = None
        self.journal[relpath] = di
        self._save_journal()

    def sync(self):

        try:
            self.journal = self._load_journal()
        except FileNotFoundError:
            self.journal = {}
        except json.decoder.JSONDecodeError:
            self.journal = {}

        self.remote = self._list_remote()
        self.local = self._list_local()

        r = set(self.remote)
        l = set(self.local)
        j = set(self.journal)

        # Exists on remote only : upload
        for relpath in (r - l) - j:
            self._receive(relpath)

        # Exists on local only : download
        for relpath in (l - r) - j:
            self._send(relpath)

        # Exists on remote and journal not on local : delete on remote and journal
        for relpath in (r & j) - l:
            self.client.clean(relpath)
            del self.journal[relpath]
            self._save_journal()

        # Exists on local and journal not on remote : delete on local and journal
        for relpath in (l & j) - r:
            local_pth = os.path.join(self.local_path, relpath)
            os.remove(local_pth)
            del self.journal[relpath]
            self._save_journal()

        # Exists on both not on journal
        for relpath in (l & r) - j:
            if self.local[relpath]["etag"] == self.remote[relpath]["etag"]:
                di = {
                    "local_etag": self.local[relpath]["etag"].strip("'\""),
                    "remote_etag": self._get_remote_etag(relpath),
                    "relpath": relpath,
                }
                with open(local_pth, "r") as fh:
                    try:
                        di["content"] = fh.read()
                    except UnicodeDecodeError:
                        di["content"] = None
                self.journal[relpath] = di
                self._save_journal()
                continue
            self._conflict_resolution(relpath)

        # Exists only in journal
        for relpath in (j - r) - l:
            del self.journal[relpath]
            self._save_journal()

        # Exists on all
        for relpath in (l & r) & j:
            l_change = (
                self.local[relpath]["etag"] != self.journal[relpath]["local_etag"]
            )
            r_change = (
                self.remote[relpath]["etag"] != self.journal[relpath]["remote_etag"]
            )
            if l_change and r_change:
                self._conflict_resolution(relpath)
            if l_change:
                self._send(relpath)
            if r_change:
                print(
                    "r_change {} : {} != {}".format(
                        r_change,
                        self.remote[relpath]["etag"],
                        self.journal[relpath]["remote_etag"],
                    )
                )
                self._receive(relpath)

    def _get_remote_content(self, relpath):

        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            print(tmp.name)
            self.client.download_sync(remote_path=relpath, local_path=tmp.name)
            content = tmp.write()
        finally:
            tmp.close()
            os.unlink(tmp.name)
        return content

    def _conflict_resolution(self, relpath):
        resolved = False
        local_pth = os.path.join(self.local_path, relpath)

        # Try a merge 3
        if os.path.splitext(relpath)[1] in ("txt", "md", "org"):
            print("Trying merge3 on {}".format(relpath))
            with open(local_pth, "r") as lfh:
                local_content = lfh.read()
            remote_content = self._get_remote_content(relpath)
            journal_content = self.journal[relpath]["content"]
            merge = merge3.Merge3(journal_content, local_content, remote_content)
            new_content = ""
            conflict = False
            for i, line in merge.merge_groups():
                if i == "conflict":
                    conflict = True
                    break
                new_content += line
            if not conflict:
                resolved = True
                with open(local_pth, "w") as lfh:
                    lfh.write(new_content)
                self.local[relpath]["etag"] = self._compute_local_etag(local_pth)
                self._send(local_pth)

        if not resolved:
            print("Conflict not resolved for %s" % relpath)
            os.rename(
                local_pth,
                "{}_{}.{}".format(
                    os.path.splitext(local_pth)[0],
                    int(time.time()),
                    os.path.splitext(local_pth)[1],
                ),
            )
            self._receive(relpath)

    def _list_local(self):
        local_dict = {}
        for root, dirs, files in os.walk(self.local_path, topdown=True):
            for name in files:
                if name.startswith("."):
                    continue
                pth = os.path.join(root, name)
                di = {"relpath": os.path.relpath(pth, self.local_path)}
                di["etag"] = WebDavSync._compute_local_etag(pth)
                local_dict[di["relpath"]] = di

        return local_dict

    def _list_remote_dir(self, d):
        remote_list = self.client.list(d, get_info=True)
        remote_dict = {}
        for remote_item in remote_list:
            if remote_item["isdir"]:
                # ignore starting with .
                if os.path.basename(remote_item["path"].rstrip("/")).startswith("."):
                    continue
                remote_dict.update(
                    self._list_remote_dir(
                        os.path.relpath(remote_item["path"], self.remote_path)
                    )
                )
            else:
                di = {
                    "relpath": os.path.relpath(remote_item["path"], self.remote_path),
                    "etag": remote_item["etag"].strip("'\""),
                }
                remote_dict[di["relpath"]] = di
        return remote_dict

    def _list_remote(self):
        """Build a remote list"""
        return self._list_remote_dir("")

    """
            remoteFiles = self._build_remote_journal()
            localFiles = self._build_local_journal()

            journal = self._load_journal()

            toUpload = []
            toDownload = []
            toLocalDelete = []
            toRemoteDelete = []

            # Delete what should be deleted
            for f in journal["local"]:
                oldF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"]),
                        localFiles,
                    ),
                    None,
                )
                if oldF is None:
                    toRemoteDelete.append(f)
            for f in journal["remote"]:
                oldF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"])
                        and d.get("isdir") is False,
                        remoteFiles,
                    ),
                    None,
                )
                if oldF is None:
                    toLocalDelete.append(f)

            # File up/down
            for f in remoteFiles:
                if f["isdir"]:
                    continue
                localF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"])
                        and f.get("isdir") is False,
                        localFiles,
                    ),
                    None,
                )
                if localF is None:
                    toDownload.append(f)
                else:
                    if localF["modified"] > f["modified"]:
                        toUpload.append(localF)
                    elif localF["modified"] < f["modified"]:
                        toDownload.append(f)

            for f in localFiles:
                if f["isdir"]:
                    continue
                remoteF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"]),
                        remoteFiles,
                    ),
                    None,
                )
                if remoteF is None:
                    toUpload.append(f)

            '''    def sync(self):
            remoteFiles = convertToEpochAndRelPath(
                self.client.list(get_info=True), self.remote_path
            )
            localFiles = self._build_local_journal()

            toUpload = []
            toDownload = []
            toLocalDelete = []
            toRemoteDelete = []

            try:
                oldJournal = self._load_journal()

                # Detect Delete
                for f in oldJournal["local"]:
                    oldF = next(
                        filter(
                            lambda d: (d.get("relpath") == f["relpath"]),
                            localFiles,
                        ),
                        None,
                    )
                    if oldF is None:
                        toRemoteDelete.append(f)
                for f in oldJournal["remote"]:
                    oldF = next(
                        filter(
                            lambda d: (d.get("relpath") == f["relpath"])
                            and d.get("isdir") is False,
                            remoteFiles,
                        ),
                        None,
                    )
                    if oldF is None:
                        toLocalDelete.append(f)

                # Detect Creation && modification
                ""for f in remoteFiles:
                    oldF = next(
                        filter(
                            lambda d: d.get("relpath") == f["relpath"], oldJournal["remote"]
                        ),
                        None,
                    )
                    if oldF is None:
                        toDownload.append(f["path"])
                for f in localFiles:
                    oldF = next(
                        filter(
                            lambda d: d.get("relpath") == f["relpath"], oldJournal["local"]
                        ),
                        None,
                    )
                    if oldF is None:
                        toUpload.append(f["relpath"])""

            except FileNotFoundError:
                self.client.pull(remote_directory="", local_directory=self.local_path)
                self._save_journal(remoteFiles, localFiles)
                return

            # File missing
            for f in remoteFiles:
                if f["relpath"].endswith("/"):
                    continue
                localF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"])
                        and f.get("isdir") is False,
                        localFiles,
                    ),
                    None,
                )
                if localF is None:
                    toDownload.append(f)
                else:
                    if localF["modified"] > f["modified"]:
                        toUpload.append(localF)
                    elif localF["modified"] < f["modified"]:
                        toDownload.append(f)

            for f in localFiles:
                # Ignore sub directory #FIXME
                if os.path.dirname(f["relpath"]) != "":
                    continue
                remoteF = next(
                    filter(
                        lambda d: (d.get("relpath") == f["relpath"]),
                        remoteFiles,
                    ),
                    None,
                )
                if remoteF is None:
                    toUpload.append(f)

            # Filter . file
            toUpload = [
                f
                for f in toUpload
                if (not os.path.basename(f["relpath"]).startswith("."))
                and (f["relpath"] not in [d["relpath"] for d in toLocalDelete])
            ]
            toDownload = [
                f
                for f in toDownload
                if (not os.path.basename(f["relpath"]).startswith("."))
                and (f["relpath"] not in [d["relpath"] for d in toRemoteDelete])
            ]
            toLocalDelete = [
                f
                for f in toLocalDelete
                if not os.path.basename(f["relpath"]).startswith(".")
            ]
            toRemoteDelete = [
                f
                for f in toRemoteDelete
                if not os.path.basename(f["relpath"]).startswith(".")
            ]

            # FIXME TAKE CARE OF FOLDER
            print("toUpload: %s" % toUpload)
            print("toDownload: %s" % toDownload)
            print("toLocalDelete: %s" % toLocalDelete)
            print("toRemoteDelete: %s" % toRemoteDelete)

            for f in toLocalDelete:
                try:
                    if os.path.exists(f["relpath"]):
                        os.remove(f["relpath"])
                except Exception as err:
                    print(err)

            for f in toRemoteDelete:
                try:
                    self.client.clean(f["relpath"])
                except Exception as err:
                    print(err)

            for f in toUpload:
                if f["relpath"] in toLocalDelete:
                    continue
                try:
                    if not os.path.exists(f["path"]):
                        continue
                    self.client.upload_sync(remote_path=f["relpath"], local_path=f["path"])
                    info = self.client.info(remote_path=f["relpath"])
                    t = time.mktime(dateutil.parser.parse(info["modified"]).timetuple())
                    os.utime(f["path"], (t, t))
                except Exception as err:
                    print(err)
                    continue

            for f in toDownload:
                if f["path"].endswith("/"):
                    continue
                self.client.download_sync(
                    remote_path=f["relpath"],
                    local_path=os.path.join(self.local_path, f["relpath"]),
                )
                os.utime(
                    os.path.join(self.local_path, f["relpath"]),
                    (f["modified"], f["modified"]),
                )

            self._save_journal(remoteFiles, localFiles)

            # Return local changes
            return toDownload
        '''
        """

    """
    def _remote_list_dir(self, d):
        alist = self.client.list(d, get_info=True)
        print(alist)
        for alistitem in alist:
            alistitem["relpath"] = os.path.relpath(alistitem["path"], self.remote_path)
            if type(alistitem["modified"]) == str:
                alistitem["modified"] = time.mktime(
                    dateutil.parser.parse(alistitem["modified"]).timetuple()
                )

            if alistitem["isdir"]:
                alist += self._remote_list_dir(alistitem["relpath"])

        return alist

    def _build_remote_journal(self):
        alist = self._remote_list_dir("")
        return alist

    def _build_local_journal(self):
        p = []
        for root, dirs, files in os.walk(self.local_path, topdown=True):
            for name in files:
                pth = os.path.join(root, name)
                p.append(
                    {
                        "modified": os.path.getmtime(pth),
                        "path": os.path.join(root, name),
                        "relpath": os.path.relpath(
                            os.path.join(root, name), self.local_path
                        ),
                    }
       
       )
        return p
    """

    def _load_journal(self):
        with open(os.path.join(self.local_path, self._journal_path), "r") as fh:
            return json.load(fh)

    def _save_journal(self):
        with open(os.path.join(self.local_path, self._journal_path), "w") as fh:
            json.dump(self.journal, fh)


if __name__ == "__main__":
    import sys

    s = WebDavSync(
        host=sys.argv[1],
        login=sys.argv[2],
        passwd=sys.argv[3],
        root=sys.argv[4],
        local_path=sys.argv[5],
    )
    s.sync()
