package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class Dataset {

    @SerializedName("name")
    protected String mName;

    public String getName() {
        return mName;
    }
}
