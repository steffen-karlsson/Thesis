package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class Dataset {

    @SerializedName("name")
    protected String mName;

    @SerializedName("description")
    protected String mDescription;

    @SerializedName("operations")
    protected List<Operation> mOperations;

    protected transient boolean mIsEven;

    public boolean isEven() {
        return mIsEven;
    }

    public void setEven(boolean isEven) {
        this.mIsEven = isEven;
    }

    public String getName() {
        return mName;
    }

    public String getDescription() {
        return mDescription;
    }

    public List<String> getOperationNames(boolean withNewLine) {
        if (mOperations == null)
            return new ArrayList<>();

        ArrayList<String> modifiedOperations = new ArrayList<>();
        for (int i = 0; i < mOperations.size(); i++) {
            String operation = mOperations.get(i).getName();
            if (withNewLine)
                modifiedOperations.add(String.format("%s" + (i != mOperations.size() - 1 ? "\n" : ""), operation));
            else
                modifiedOperations.add(operation);
        }
        return modifiedOperations;
    }

    public List<Operation> getOperations() {
        return mOperations;
    }
}
