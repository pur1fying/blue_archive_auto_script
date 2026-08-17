package org.baas.boa;

import android.os.Parcel;
import android.os.Parcelable;

public class FsReadResult implements Parcelable {
    public boolean isBase64;
    public String text;    // 当 isBase64=false 时有效
    public byte[] bytes;   // 当 isBase64=true 时有效

    public FsReadResult() {}

    protected FsReadResult(Parcel in) {
        isBase64 = in.readByte() != 0;
        text = in.readString();
        bytes = in.createByteArray();
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeByte((byte) (isBase64 ? 1 : 0));
        dest.writeString(text);
        dest.writeByteArray(bytes);
    }

    @Override
    public int describeContents() { return 0; }

    public static final Creator<FsReadResult> CREATOR = new Creator<FsReadResult>() {
        @Override
        public FsReadResult createFromParcel(Parcel in) { return new FsReadResult(in); }
        @Override
        public FsReadResult[] newArray(int size) { return new FsReadResult[size]; }
    };
}


