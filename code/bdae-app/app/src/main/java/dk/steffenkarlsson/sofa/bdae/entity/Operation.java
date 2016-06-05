package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

/**
 * Created by steffenkarlsson on 6/5/16.
 */
public class Operation {

    @SerializedName("name")
    protected String mName;

    @SerializedName("num_arguments")
    protected int mNumArguments;

    public String getName() {
        return mName;
    }

    public int getNumArguments() {
        return mNumArguments;
    }

    public boolean hasArguments() {
        return mNumArguments > 0;
    }
}
