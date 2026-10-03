package org.baas.boa;

import android.os.Parcel;
import android.os.Parcelable;

public class FsStat implements Parcelable {
    public boolean exists;
    public boolean isDir;
    public long size;
    public long mtime;
    public Integer mode; // Optional
    public Integer uid;  // Optional
    public Integer gid;  // Optional

    public FsStat() {}

    protected FsStat(Parcel in) {
        exists = in.readByte() != 0;
        isDir = in.readByte() != 0;
        size = in.readLong();
        mtime = in.readLong();
        mode = (Integer) (in.readByte() == 0 ? null : in.readInt());
        uid = (Integer) (in.readByte() == 0 ? null : in.readInt());
        gid = (Integer) (in.readByte() == 0 ? null : in.readInt());
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeByte((byte) (exists ? 1 : 0));
        dest.writeByte((byte) (isDir ? 1 : 0));
        dest.writeLong(size);
        dest.writeLong(mtime);
        if (mode == null) { dest.writeByte((byte)0); } else { dest.writeByte((byte)1); dest.writeInt(mode); }
        if (uid == null) { dest.writeByte((byte)0); } else { dest.writeByte((byte)1); dest.writeInt(uid); }
        if (gid == null) { dest.writeByte((byte)0); } else { dest.writeByte((byte)1); dest.writeInt(gid); }
    }

    @Override
    public int describeContents() { return 0; }

    public static final Creator<FsStat> CREATOR = new Creator<FsStat>() {
        @Override
        public FsStat createFromParcel(Parcel in) { return new FsStat(in); }
        @Override
        public FsStat[] newArray(int size) { return new FsStat[size]; }
    };
}


