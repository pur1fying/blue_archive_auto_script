package org.baas.boa;

import android.os.Parcel;
import android.os.Parcelable;

public class CommandResult implements Parcelable {
    public int exitCode;
    public String stdout;
    public String stderr;

    public CommandResult() {}

    protected CommandResult(Parcel in) {
        exitCode = in.readInt();
        stdout = in.readString();
        stderr = in.readString();
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeInt(exitCode);
        dest.writeString(stdout);
        dest.writeString(stderr);
    }

    @Override
    public int describeContents() { return 0; }

    public static final Creator<CommandResult> CREATOR = new Creator<CommandResult>() {
        @Override
        public CommandResult createFromParcel(Parcel in) { return new CommandResult(in); }
        @Override
        public CommandResult[] newArray(int size) { return new CommandResult[size]; }
    };
}


